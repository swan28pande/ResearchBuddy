"""Research workflow: plan -> run subtasks in parallel -> synthesize a cited report.

    START -> planner --Send x N--> execute_subtask (one per subtask, in parallel) -> synthesizer -> END

* planner: an LLM breaks the query into up to MAX_SUBTASKS subtasks, each tagged
  with a tool category (web_search, academic_search, code_execution, ...).
* execute_subtask: LangGraph's Send API starts one copy per subtask; they run in
  the same step, concurrently. Each calls the ToolRouter (retry + fallback).
  Results are merged into state by the `operator.add` reducer.
* synthesizer: numbers every source, asks the LLM to cite them inline as [n], and
  appends a References list built from the real tool results, so links are never
  made up by the model.
"""

import json
import logging
import operator
import os
import re
from typing import Annotated, Any, Callable, Dict, List, Optional, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from tools import CATEGORIES, ToolRouter, build_default_registry

load_dotenv()
logger = logging.getLogger(__name__)

MAX_SUBTASKS = int(os.getenv("MAX_SUBTASKS", "5"))
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "5"))
SOURCES_PER_SUBTASK = 5
LLM_MODEL = os.getenv("LLM_MODEL", "openai:gpt-4.1")


class ResearchState(TypedDict, total=False):
    query: str
    subtasks: List[Dict[str, Any]]
    results: Annotated[List[Dict[str, Any]], operator.add]
    sources: List[Dict[str, Any]]
    report: str


class SubtaskState(TypedDict):
    subtask: Dict[str, Any]


def default_llm():
    from langchain.chat_models import init_chat_model
    return init_chat_model(LLM_MODEL, temperature=0)


def _text(response) -> str:
    return response.content if hasattr(response, "content") else str(response)


# ---------------------------------------------------------------- planner

PLANNER_PROMPT = """You are the planner of a research assistant. Break the user's query into at most {max_subtasks} independent subtasks that can run in parallel. Pick the best tool category for each.

Tool categories:
{categories}

Rules:
- Use a mix of categories when it helps (for example web_search for context and academic_search for papers).
- "input" is what the tool receives: a short search query for search categories, Python code that prints its answer for code_execution, a URL for document_parsing.
- Only use code_execution when a number needs computing, and document_parsing only for a URL the user gave.

Return ONLY JSON in this shape:
{{"subtasks": [{{"id": 1, "goal": "what this subtask finds out", "category": "web_search", "input": "search query"}}]}}

User query: {query}"""


def _extract_json(text: str) -> Optional[dict]:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def fallback_plan(query: str) -> List[Dict[str, Any]]:
    return [
        {"id": 1, "goal": "Background and recent developments", "category": "web_search", "input": query},
        {"id": 2, "goal": "Research literature", "category": "academic_search", "input": query},
    ]


def parse_plan(text: str, query: str, allowed: List[str], max_subtasks: int = MAX_SUBTASKS) -> List[Dict[str, Any]]:
    """Validate the planner's JSON; drop bad subtasks; fall back to a default plan if nothing usable is left."""
    data = _extract_json(text) or {}
    subtasks = []
    for st in data.get("subtasks", []) if isinstance(data, dict) else []:
        if not isinstance(st, dict):
            continue
        category, tool_input = st.get("category"), str(st.get("input") or "").strip()
        if category not in allowed or not tool_input:
            continue
        subtasks.append({
            "id": len(subtasks) + 1,
            "goal": str(st.get("goal") or tool_input)[:200],
            "category": category,
            "input": tool_input,
        })
        if len(subtasks) == max_subtasks:
            break
    if not subtasks:
        logger.warning("Planner output unusable, using fallback plan")
        return [s for s in fallback_plan(query) if s["category"] in allowed]
    return subtasks


# ---------------------------------------------------------------- synthesizer

SYNTH_PROMPT = """Write a detailed research report in Markdown that answers the query below, using ONLY the numbered sources.

Query: {query}

Subtasks that were researched:
{subtasks}

Sources:
{sources}

Requirements:
- Start with a short Table of Contents (no links), then sections with ## headings, then a Conclusion.
- Cite sources inline with their numbers, like [1] or [2][5]. Every factual claim needs a citation.
- If the sources don't cover part of the query, say so instead of guessing.
- Do NOT write a references list; it is appended automatically."""


def collect_sources(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten subtask results into one numbered, de-duplicated source list."""
    sources, seen = [], set()
    for res in sorted(results, key=lambda r: r["subtask"]["id"]):
        for src in res["route"]["results"][:SOURCES_PER_SUBTASK]:
            key = src.get("url") or (src.get("title"), src.get("snippet"))
            if key in seen:
                continue
            seen.add(key)
            sources.append({**src, "n": len(sources) + 1, "subtask_id": res["subtask"]["id"]})
    return sources


def format_reference(src: Dict[str, Any]) -> str:
    meta = src.get("metadata") or {}
    line = f"[{src['n']}] {(src.get('title') or 'Untitled').rstrip('.')}"
    if meta.get("authors"):
        line += f". {meta['authors']}"
    if meta.get("year"):
        line += f" ({meta['year']})"
    if src.get("url"):
        line += f". <{src['url']}>"
    return line + f" _(via {src['tool']})_"


def references_section(sources: List[Dict[str, Any]]) -> str:
    if not sources:
        return "\n\n## References\n\nNo sources could be retrieved.\n"
    return "\n\n## References\n\n" + "\n\n".join(format_reference(s) for s in sources) + "\n"


def tool_log_section(results: List[Dict[str, Any]]) -> str:
    lines = []
    for res in sorted(results, key=lambda r: r["subtask"]["id"]):
        st, route = res["subtask"], res["route"]
        tried = " → ".join(f"{a['tool']}{'' if a['ok'] else ' ✗'}" for a in route["attempts"]) or "no tool available"
        lines.append(f"- **{st['goal']}** ({st['category']}): {tried}")
    return "\n## How this report was researched\n\n" + "\n".join(lines) + "\n"


# ---------------------------------------------------------------- graph

def build_graph(llm=None, router: Optional[ToolRouter] = None):
    llm = llm or default_llm()
    router = router or ToolRouter(build_default_registry())
    allowed = [c for c in CATEGORIES if any(t.available() for t in router.registry.by_category(c))]

    def planner(state: ResearchState):
        categories = "\n".join(f"- {c}: {CATEGORIES[c]}" for c in allowed)
        prompt = PLANNER_PROMPT.format(max_subtasks=MAX_SUBTASKS, categories=categories, query=state["query"])
        try:
            text = _text(llm.invoke(prompt))
        except Exception as e:
            logger.error("Planner LLM call failed: %s", e)
            text = ""
        return {"subtasks": parse_plan(text, state["query"], allowed)}

    def fan_out(state: ResearchState):
        # One Send per subtask: LangGraph runs all of them in the same step, in parallel.
        return [Send("execute_subtask", {"subtask": st}) for st in state["subtasks"]]

    def execute_subtask(state: SubtaskState):
        st = state["subtask"]
        route = router.run(st["category"], st["input"])
        return {"results": [{"subtask": st, "route": route.to_dict()}]}

    def synthesizer(state: ResearchState):
        results = state.get("results", [])
        sources = collect_sources(results)
        subtasks = "\n".join(f"{s['id']}. {s['goal']}" for s in state["subtasks"])
        source_text = "\n\n".join(
            f"[{s['n']}] {s['title']}" + (f" ({s['url']})" if s.get("url") else "") + f"\n{s['snippet']}"
            for s in sources
        ) or "(no sources were retrieved)"
        try:
            body = _text(llm.invoke(SYNTH_PROMPT.format(query=state["query"], subtasks=subtasks, sources=source_text)))
        except Exception as e:
            logger.error("Synthesizer LLM call failed: %s", e)
            body = f"# {state['query']}\n\nThe report could not be written ({e}). The sources found are listed below."
        report = body.rstrip() + references_section(sources) + tool_log_section(results)
        return {"sources": sources, "report": report}

    g = StateGraph(ResearchState)
    g.add_node("planner", planner)
    g.add_node("execute_subtask", execute_subtask)
    g.add_node("synthesizer", synthesizer)
    g.add_edge(START, "planner")
    g.add_conditional_edges("planner", fan_out, ["execute_subtask"])
    g.add_edge("execute_subtask", "synthesizer")
    g.add_edge("synthesizer", END)
    return g.compile()


def run_research(
    query: str,
    llm=None,
    router: Optional[ToolRouter] = None,
    on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    max_concurrency: int = MAX_CONCURRENCY,
) -> Dict[str, Any]:
    """Run the workflow and return the final state. `on_event(node, update)` fires after each node."""
    graph = build_graph(llm, router)
    final: Dict[str, Any] = {}
    for mode, chunk in graph.stream(
        {"query": query, "results": []},
        config={"max_concurrency": max_concurrency},
        stream_mode=["updates", "values"],
    ):
        if mode == "values":
            final = chunk
        elif on_event:
            for node, update in chunk.items():
                on_event(node, update or {})
    return final


def build_and_run_workflow(query: str, generate_pdf: bool = True) -> str:
    """Kept for existing callers (main.py, app.py): returns just the report text."""
    return run_research(query)["report"]
