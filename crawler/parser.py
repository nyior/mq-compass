from __future__ import annotations

from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def extract_page_data(html: str, base_url: str, allowed_domains: set[str]) -> tuple[str, str, set[str]]:
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else ""
    body_text = soup.body.get_text(" ", strip=True) if soup.body else soup.get_text(" ", strip=True)
    text = normalize_text(body_text)

    links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        joined = urljoin(base_url, anchor["href"])
        clean_url = urldefrag(joined).url
        parsed = urlparse(clean_url)

        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc not in allowed_domains:
            continue

        normalized = parsed._replace(query="").geturl().rstrip("/")
        links.add(normalized)

    return title, text, links
