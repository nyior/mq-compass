from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from .parser import extract_page_data
from .queue import QueuePublisher
from .storage import PageStorage


SEED_URLS = [
    "https://lavinmq.com/documentation//blog/",
    "https://lavinmq.com/blog",
]


@dataclass
class CrawlResult:
    crawled: int
    new: int
    changed: int
    unchanged: int
    queued: int
    errors: list[dict[str, str]]


class SimpleCrawler:
    def __init__(self, storage: PageStorage, publisher: QueuePublisher) -> None:
        self.storage = storage
        self.publisher = publisher

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)
        return parsed._replace(query="", fragment="").geturl().rstrip("/")

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def run(self, max_pages: int = 50) -> CrawlResult:
        normalized_seeds = [self._normalize_url(url) for url in SEED_URLS]
        allowed_domains = {urlparse(url).netloc for url in normalized_seeds}

        queue: deque[str] = deque(normalized_seeds)
        visited: set[str] = set()

        new_count = 0
        changed_count = 0
        unchanged_count = 0
        queued_count = 0
        errors: list[dict[str, str]] = []

        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            while queue and len(visited) < max_pages:
                url = queue.popleft()
                if url in visited:
                    continue

                visited.add(url)

                try:
                    response = client.get(url)
                    response.raise_for_status()
                except Exception as exc:  # noqa: BLE001
                    errors.append({"url": url, "error": str(exc)})
                    continue

                title, text, links = extract_page_data(response.text, url, allowed_domains)
                page_hash = self._hash_text(text)

                previous = self.storage.get_page(url)
                if previous is None:
                    status = "new"
                    new_count += 1
                elif previous["content_hash"] != page_hash:
                    status = "changed"
                    changed_count += 1
                else:
                    status = "unchanged"
                    unchanged_count += 1

                self.storage.upsert_page(url=url, content_hash=page_hash, status=status)

                if status in {"new", "changed"}:
                    payload = {
                        "url": url,
                        "content_hash": page_hash,
                        "event": "page_updated",
                        "title": title,
                    }
                    self.publisher.publish(payload)
                    self.storage.set_status(url, "queued")
                    queued_count += 1

                for link in links:
                    if link not in visited:
                        queue.append(link)

        return CrawlResult(
            crawled=len(visited),
            new=new_count,
            changed=changed_count,
            unchanged=unchanged_count,
            queued=queued_count,
            errors=errors,
        )
