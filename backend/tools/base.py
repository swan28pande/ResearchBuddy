"""Common interface every tool integration implements.

A tool takes one string input (a search query, a URL, or a code snippet) and
returns a list of Source dicts. Because every tool has the same shape, agents
never depend on a specific API and the router can swap one tool for another.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# Tool categories the planner can route subtasks to.
WEB_SEARCH = "web_search"
ACADEMIC_SEARCH = "academic_search"
CODE_SEARCH = "code_search"
DISCUSSION_SEARCH = "discussion_search"
CODE_EXECUTION = "code_execution"
DOCUMENT_PARSING = "document_parsing"

CATEGORIES = {
    WEB_SEARCH: "General web search for facts, news and overviews",
    ACADEMIC_SEARCH: "Peer-reviewed papers and preprints",
    CODE_SEARCH: "Open-source repositories and implementations",
    DISCUSSION_SEARCH: "Practitioner discussion and opinions",
    CODE_EXECUTION: "Run a short Python snippet to compute or verify a number (input is Python code that prints its result)",
    DOCUMENT_PARSING: "Extract the text of a PDF or web page (input is a URL)",
}


class ToolError(Exception):
    """Raised by a tool when a call fails. `retryable=False` skips straight to fallback."""

    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


@dataclass
class Source:
    title: str
    url: str = ""
    snippet: str = ""
    tool: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Tool:
    """Base class. Subclasses set `name`, `category`, `description` and implement `_run`."""

    name: str = ""
    category: str = ""
    description: str = ""
    # Lower runs first when the router falls back across a category.
    priority: int = 100
    timeout: float = 20.0

    def available(self) -> bool:
        """False when the tool can't run here (for example, a missing API key). The router skips it."""
        return True

    def run(self, tool_input: str) -> List[Source]:
        results = self._run(tool_input)
        for r in results:
            r.tool = r.tool or self.name
        return results

    def _run(self, tool_input: str) -> List[Source]:  # pragma: no cover - abstract
        raise NotImplementedError

    def info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "priority": self.priority,
            "available": self.available(),
        }


def truncate(text: Optional[str], limit: int = 800) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def http_error(response) -> ToolError:
    """4xx (except 429 rate limiting) won't fix itself on retry; 5xx and 429 might."""
    retryable = response.status_code >= 500 or response.status_code == 429
    return ToolError(f"HTTP {response.status_code}", retryable=retryable)
