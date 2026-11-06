import os
import xml.etree.ElementTree as ET
from typing import List

from .base import ACADEMIC_SEARCH, Source, Tool, ToolError, http_error, truncate
from .http import DEFAULT_TIMEOUT, session, strip_html


def _authors(names: List[str]) -> str:
    names = [n for n in names if n]
    return ", ".join(names[:3]) + (" et al." if len(names) > 3 else "")


class SemanticScholarSearch(Tool):
    name = "semantic_scholar"
    category = ACADEMIC_SEARCH
    description = "Semantic Scholar paper search (key optional; rate-limited without one)"
    priority = 10

    def __init__(self, api_key: str = None, max_results: int = 5):
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.max_results = max_results

    def _run(self, query: str) -> List[Source]:
        s = session()
        if self.api_key:
            s.headers["x-api-key"] = self.api_key
        r = s.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={"query": query, "limit": self.max_results,
                    "fields": "title,authors,year,abstract,url,citationCount"},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code != 200:
            raise http_error(r)
        return [
            Source(
                title=p.get("title") or "",
                url=p.get("url") or "",
                snippet=truncate(p.get("abstract") or ""),
                metadata={
                    "authors": _authors([a.get("name") for a in p.get("authors", [])]),
                    "year": p.get("year"),
                    "citations": p.get("citationCount"),
                },
            )
            for p in r.json().get("data", []) or []
        ]


class ArxivSearch(Tool):
    name = "arxiv"
    category = ACADEMIC_SEARCH
    description = "arXiv preprint search (no key)"
    priority = 20
    NS = {"atom": "http://www.w3.org/2005/Atom"}

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def _run(self, query: str) -> List[Source]:
        r = session().get(
            "http://export.arxiv.org/api/query",
            params={"search_query": f"all:{query}", "start": 0, "max_results": self.max_results,
                    "sortBy": "relevance", "sortOrder": "descending"},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code != 200:
            raise http_error(r)
        try:
            root = ET.fromstring(r.content)
        except ET.ParseError as e:
            raise ToolError(f"bad XML: {e}")
        out = []
        for e in root.findall("atom:entry", self.NS):
            text = lambda tag: (e.findtext(tag, default="", namespaces=self.NS) or "").strip()
            abs_url = text("atom:id")
            out.append(Source(
                title=" ".join(text("atom:title").split()),
                url=abs_url,
                snippet=truncate(text("atom:summary")),
                metadata={
                    "authors": _authors([a.findtext("atom:name", namespaces=self.NS) for a in e.findall("atom:author", self.NS)]),
                    "year": text("atom:published")[:4],
                    "arxiv_id": abs_url.rsplit("/", 1)[-1],
                },
            ))
        return out


class OpenAlexSearch(Tool):
    name = "openalex"
    category = ACADEMIC_SEARCH
    description = "OpenAlex scholarly works index (no key)"
    priority = 30

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    @staticmethod
    def _abstract(inverted):
        # OpenAlex stores abstracts as {word: [positions]}; rebuild the text.
        if not inverted:
            return ""
        words = sorted((pos, w) for w, positions in inverted.items() for pos in positions)
        return " ".join(w for _, w in words)

    def _run(self, query: str) -> List[Source]:
        r = session().get(
            "https://api.openalex.org/works",
            params={"search": query, "per-page": self.max_results},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code != 200:
            raise http_error(r)
        out = []
        for w in r.json().get("results", []):
            out.append(Source(
                title=w.get("display_name") or "",
                url=w.get("doi") or w.get("id") or "",
                snippet=truncate(self._abstract(w.get("abstract_inverted_index"))),
                metadata={
                    "authors": _authors([a.get("author", {}).get("display_name") for a in w.get("authorships", [])]),
                    "year": w.get("publication_year"),
                    "citations": w.get("cited_by_count"),
                },
            ))
        return out


class CrossrefSearch(Tool):
    name = "crossref"
    category = ACADEMIC_SEARCH
    description = "Crossref DOI metadata search (no key)"
    priority = 40

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def _run(self, query: str) -> List[Source]:
        r = session().get(
            "https://api.crossref.org/works",
            params={"query": query, "rows": self.max_results,
                    "select": "DOI,title,author,issued,abstract,URL"},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code != 200:
            raise http_error(r)
        out = []
        for it in r.json().get("message", {}).get("items", []):
            year = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
            out.append(Source(
                title=(it.get("title") or [""])[0],
                url=it.get("URL") or f"https://doi.org/{it.get('DOI', '')}",
                snippet=truncate(strip_html(it.get("abstract", ""))),
                metadata={
                    "authors": _authors([f"{a.get('given', '')} {a.get('family', '')}".strip() for a in it.get("author", [])]),
                    "year": year,
                    "doi": it.get("DOI"),
                },
            ))
        return out


class PubMedSearch(Tool):
    name = "pubmed"
    category = ACADEMIC_SEARCH
    description = "PubMed biomedical literature via NCBI E-utilities (no key)"
    priority = 50
    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def _run(self, query: str) -> List[Source]:
        s = session()
        r = s.get(f"{self.BASE}/esearch.fcgi",
                  params={"db": "pubmed", "term": query, "retmax": self.max_results, "retmode": "json"},
                  timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:
            raise http_error(r)
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        r = s.get(f"{self.BASE}/esummary.fcgi",
                  params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
                  timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:
            raise http_error(r)
        result = r.json().get("result", {})
        out = []
        for pmid in ids:
            doc = result.get(pmid, {})
            out.append(Source(
                title=doc.get("title", ""),
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                snippet=truncate(f"{doc.get('fulljournalname', '')}, {doc.get('pubdate', '')}"),
                metadata={
                    "authors": _authors([a.get("name") for a in doc.get("authors", [])]),
                    "year": (doc.get("pubdate") or "")[:4],
                    "pmid": pmid,
                },
            ))
        return out
