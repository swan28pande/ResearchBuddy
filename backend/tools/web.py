import os
from typing import List

from .base import Source, Tool, ToolError, WEB_SEARCH, http_error, truncate
from .http import DEFAULT_TIMEOUT, session, strip_html


class TavilySearch(Tool):
    name = "tavily"
    category = WEB_SEARCH
    description = "Tavily web search API (needs TAVILY_API_KEY)"
    priority = 10

    def __init__(self, api_key: str = None, max_results: int = 5):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.max_results = max_results

    def available(self) -> bool:
        return bool(self.api_key)

    def _run(self, query: str) -> List[Source]:
        r = session().post(
            "https://api.tavily.com/search",
            json={"query": query, "max_results": self.max_results},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code != 200:
            raise http_error(r)
        return [
            Source(title=x.get("title", ""), url=x.get("url", ""), snippet=truncate(x.get("content")))
            for x in r.json().get("results", [])
        ]


class WikipediaSearch(Tool):
    name = "wikipedia"
    category = WEB_SEARCH
    description = "Wikipedia article search (no key)"
    priority = 20

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def _run(self, query: str) -> List[Source]:
        r = session().get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query", "list": "search", "srsearch": query,
                "srlimit": self.max_results, "format": "json",
            },
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code != 200:
            raise http_error(r)
        hits = r.json().get("query", {}).get("search", [])
        return [
            Source(
                title=h["title"],
                url="https://en.wikipedia.org/wiki/" + h["title"].replace(" ", "_"),
                snippet=truncate(strip_html(h.get("snippet", ""))),
            )
            for h in hits
        ]


class DuckDuckGoSearch(Tool):
    name = "duckduckgo"
    category = WEB_SEARCH
    description = "DuckDuckGo Instant Answer API (no key; best for well-known topics)"
    priority = 30

    def _run(self, query: str) -> List[Source]:
        r = session().get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code != 200:
            raise http_error(r)
        try:
            data = r.json()
        except ValueError:
            raise ToolError("non-JSON response")
        out = []
        if data.get("AbstractText"):
            out.append(Source(
                title=data.get("Heading") or query,
                url=data.get("AbstractURL", ""),
                snippet=truncate(data["AbstractText"]),
            ))
        for t in data.get("RelatedTopics", []):
            if "Text" in t and t.get("FirstURL"):
                out.append(Source(title=t["Text"][:80], url=t["FirstURL"], snippet=truncate(t["Text"])))
            if len(out) >= 5:
                break
        return out
