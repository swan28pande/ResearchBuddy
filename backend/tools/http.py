import re
from html import unescape

import requests

USER_AGENT = "ResearchBuddy/1.0 (research assistant)"
DEFAULT_TIMEOUT = 15


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


_TAG = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    return unescape(_TAG.sub("", text or ""))
