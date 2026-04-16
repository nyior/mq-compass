from dataclasses import dataclass
import hashlib
import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup, Tag


@dataclass
class ParsedPage:
    url: str
    title: str
    source_type: str
    main_html: str
    main_text: str
    normalized_text_hash: str


_CONTAINER_SELECTORS = [
    "main",
    "article",
    '[role="main"]',
    ".docs-content",
    ".documentation",
    ".main-content",
    ".article-content",
    ".post-content",
    "#content",
    "#main-content",
]


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _pick_main_container(soup: BeautifulSoup) -> Tag:
    for selector in _CONTAINER_SELECTORS:
        candidate = soup.select_one(selector)
        if candidate and candidate.get_text(strip=True):
            return candidate

    if soup.body:
        return soup.body
    return soup


def _infer_source_type(url: str) -> str:
    path = urlparse(url).path.lower()
    if "blog" in path:
        return "blog"
    return "docs"


def fetch_and_parse_page(url: str, timeout_seconds: float = 20.0) -> ParsedPage:
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    main_container = _pick_main_container(soup)

    title = soup.title.get_text(strip=True) if soup.title else url
    main_html = str(main_container)
    main_text = main_container.get_text(separator="\n", strip=True)

    normalized = _normalize_text(main_text)
    normalized_text_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    return ParsedPage(
        url=url,
        title=title,
        source_type=_infer_source_type(url),
        main_html=main_html,
        main_text=main_text,
        normalized_text_hash=normalized_text_hash,
    )
