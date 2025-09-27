import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

from agents.prompt_manager import PromptManagerAgent
from agents.internet_search import InternetSearchAgent
from agents.publication_search import PublicationSearchAgent
from agents.summarizer import SummarizerAgent
from agents.report_generator import ReportGeneratorAgent
from api_clients.tavily import TavilyClient
from api_clients.semantic_scholar import SemanticScholarClient
from api_clients.arxiv import ArxivClient

load_dotenv()

class ResearchState(TypedDict):
    query: str
    prompt_results:str
    web_results: list
    pub_results: list
    summary: str
    report: str

def build_and_run_workflow(query: str, generate_pdf: bool = True):
    # Instantiate API clients
    tavily_client = TavilyClient(os.getenv("TAVILY_API_KEY"))
    semscholar_client = SemanticScholarClient(os.getenv("SEMANTIC_SCHOLAR_API_KEY"))
    arxiv_client = ArxivClient()

    # Instantiate agents

    prompt_manager = PromptManagerAgent()
    internet_agent = InternetSearchAgent(tavily_client)
    # pub_agent = PublicationSearchAgent([semscholar_client, arxiv_client])
    pub_agent = PublicationSearchAgent([arxiv_client])
    summarizer = SummarizerAgent()
    reporter = ReportGeneratorAgent()

    # Define node functions

    def prompt_node(state: ResearchState):
        return {"prompt_results": prompt_manager.prompt_creation(state["query"])}
    
    def internet_search_node(state: ResearchState):
        return {"web_results": internet_agent.search(state["prompt_results"])}

    def publication_search_node(state: ResearchState):
        return {"pub_results": pub_agent.search(state["prompt_results"])}

    def summarizer_node(state: ResearchState):
        return {"summary": summarizer.summarize(state["web_results"], state["pub_results"])}

    def report_generator_node(state: ResearchState):
        return {"report": reporter.generate_report(
            state["prompt_results"], state["summary"], state["web_results"], state["pub_results"]
        )}

    graph_builder = StateGraph(ResearchState)
    graph_builder.add_node("prompt_manager", prompt_node)
    graph_builder.add_node("internet_search", internet_search_node)
    graph_builder.add_node("publication_search", publication_search_node)
    graph_builder.add_node("summarizer", summarizer_node)
    graph_builder.add_node("report_generator", report_generator_node)

    graph_builder.add_edge(START, "prompt_manager")
    graph_builder.add_edge("prompt_manager", "internet_search")
    graph_builder.add_edge("prompt_manager", "publication_search")
    graph_builder.add_edge("internet_search", "summarizer")
    graph_builder.add_edge("publication_search", "summarizer")
    graph_builder.add_edge("summarizer", "report_generator")
    graph_builder.add_edge("report_generator", END)

    graph = graph_builder.compile()
    initial_state = {"query": query}
    result = graph.invoke(initial_state)
    report_text = result["report"]
    return report_text