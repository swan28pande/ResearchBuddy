import io
from html.parser import HTMLParser
from typing import List

from .base import DOCUMENT_PARSING, Source, Tool, ToolError, http_error, truncate
from .http import DEFAULT_TIMEOUT, session

MAX_BYTES = 15_000_000


def _fetch(url: str):
    if not url.startswith(("http://", "https://")):
        raise ToolError("input must be an http(s) URL", retryable=False)
    r = session().get(url, timeout=DEFAULT_TIMEOUT, stream=True)
    if r.status_code != 200:
        raise http_error(r)
    data = r.raw.read(MAX_BYTES + 1, decode_content=True)
    if len(data) > MAX_BYTES:
        raise ToolError("document too large", retryable=False)
    return r.headers.get("Content-Type", ""), data


class PDFReader(Tool):
    name = "pdf_reader"
    category = DOCUMENT_PARSING
    description = "Downloads a PDF and extracts its text (pypdf)"
    priority = 10
    timeout = 40

    def __init__(self, max_pages: int = 15, max_chars: int = 6000):
        self.max_pages = max_pages
        self.max_chars = max_chars

    def _run(self, url: str) -> List[Source]:
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError

        content_type, data = _fetch(url.strip())
        if "pdf" not in content_type.lower() and not data.startswith(b"%PDF"):
            # Not a PDF: let the router fall back to the HTML reader.
            raise ToolError(f"not a PDF ({content_type or 'unknown type'})", retryable=False)
        try:
            reader = PdfReader(io.BytesIO(data))
            pages = [p.extract_text() or "" for p in reader.pages[: self.max_pages]]
        except PdfReadError as e:
            raise ToolError(f"could not parse PDF: {e}", retryable=False)
        title = (reader.metadata or {}).get("/Title") or url.rsplit("/", 1)[-1]
        return [Source(
            title=str(title), url=url,
            snippet=truncate("\n".join(pages), self.max_chars),
            metadata={"pages": len(reader.pages)},
        )]


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "nav", "footer", "header", "svg"}

    def __init__(self):
        super().__init__()
        self.parts, self.title, self._skip, self._in_title = [], "", 0, False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        self._in_title = tag == "title"

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip and data.strip():
            self.parts.append(data.strip())


class WebPageReader(Tool):
    name = "web_page_reader"
    category = DOCUMENT_PARSING
    description = "Downloads an HTML page and extracts its readable text"
    priority = 20

    def __init__(self, max_chars: int = 6000):
        self.max_chars = max_chars

    def _run(self, url: str) -> List[Source]:
        content_type, data = _fetch(url.strip())
        if "html" not in content_type.lower() and "text" not in content_type.lower():
            raise ToolError(f"unsupported content type {content_type}", retryable=False)
        parser = _TextExtractor()
        parser.feed(data.decode("utf-8", errors="replace"))
        text = " ".join(parser.parts)
        if not text:
            return []
        return [Source(title=parser.title.strip() or url, url=url, snippet=truncate(text, self.max_chars))]
