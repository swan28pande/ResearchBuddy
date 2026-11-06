import os
from typing import List

from .base import CODE_SEARCH, DISCUSSION_SEARCH, Source, Tool, http_error, truncate
from .http import DEFAULT_TIMEOUT, session


class GitHubSearch(Tool):
    name = "github"
    category = CODE_SEARCH
    description = "GitHub repository search (GITHUB_TOKEN optional, raises rate limit)"
    priority = 10

    def __init__(self, token: str = None, max_results: int = 5):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.max_results = max_results

    def _run(self, query: str) -> List[Source]:
        s = session()
        s.headers["Accept"] = "application/vnd.github+json"
        if self.token:
            s.headers["Authorization"] = f"Bearer {self.token}"
        r = s.get("https://api.github.com/search/repositories",
                  params={"q": query, "sort": "stars", "per_page": self.max_results},
                  timeout=DEFAULT_TIMEOUT)
        if r.status_code == 403:  # GitHub signals rate limiting with 403
            r.status_code = 429
        if r.status_code != 200:
            raise http_error(r)
        return [
            Source(
                title=repo["full_name"],
                url=repo["html_url"],
                snippet=truncate(repo.get("description") or ""),
                metadata={"stars": repo.get("stargazers_count"), "language": repo.get("language")},
            )
            for repo in r.json().get("items", [])
        ]


class HackerNewsSearch(Tool):
    name = "hackernews"
    category = DISCUSSION_SEARCH
    description = "Hacker News stories via the Algolia API (no key)"
    priority = 10

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def _run(self, query: str) -> List[Source]:
        r = session().get("https://hn.algolia.com/api/v1/search",
                          params={"query": query, "tags": "story", "hitsPerPage": self.max_results},
                          timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:
            raise http_error(r)
        return [
            Source(
                title=h.get("title") or "",
                url=h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                snippet=truncate(f"{h.get('points', 0)} points, {h.get('num_comments', 0)} comments"),
                metadata={"hn_id": h["objectID"], "year": (h.get("created_at") or "")[:4]},
            )
            for h in r.json().get("hits", [])
        ]
