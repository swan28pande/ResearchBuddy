"""Pluggable tool layer: tools share one interface, the registry holds them, the router picks one."""

from .academic import ArxivSearch, CrossrefSearch, OpenAlexSearch, PubMedSearch, SemanticScholarSearch
from .base import CATEGORIES, Source, Tool, ToolError
from .code import PythonExecutor
from .community import GitHubSearch, HackerNewsSearch
from .documents import PDFReader, WebPageReader
from .registry import ToolRegistry
from .router import RouteResult, ToolRouter
from .web import DuckDuckGoSearch, TavilySearch, WikipediaSearch

DEFAULT_TOOLS = [
    TavilySearch, WikipediaSearch, DuckDuckGoSearch,                              # web_search
    SemanticScholarSearch, ArxivSearch, OpenAlexSearch, CrossrefSearch, PubMedSearch,  # academic_search
    GitHubSearch,                                                                 # code_search
    HackerNewsSearch,                                                             # discussion_search
    PythonExecutor,                                                               # code_execution
    PDFReader, WebPageReader,                                                     # document_parsing
]


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for cls in DEFAULT_TOOLS:
        registry.register(cls())
    return registry


__all__ = [
    "CATEGORIES", "DEFAULT_TOOLS", "RouteResult", "Source", "Tool", "ToolError",
    "ToolRegistry", "ToolRouter", "build_default_registry",
]
