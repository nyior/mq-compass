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
    "https://lavinmq.com/blog",
    "https://lavinmq.com/documentation",
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

    @staticmethod
    def _belongs_to_seed(url: str, seed_url: str) -> bool:
        return url == seed_url or url.startswith(f"{seed_url}/")

    @staticmethod
    def _source_type_from_seed(seed_url: str) -> str:
        seed_path = urlparse(seed_url).path.strip("/")
        return "blog" if seed_path.startswith("blog") else "docs"

    def run(self, max_pages: int = 50) -> CrawlResult:
        normalized_seeds = [self._normalize_url(url) for url in SEED_URLS]
        allowed_domains = {urlparse(url).netloc for url in normalized_seeds}

        frontier_by_seed: dict[str, deque[str]] = {
            seed_url: deque([seed_url]) for seed_url in normalized_seeds
        }
        visited: set[str] = set()
        queued_urls: set[str] = set(normalized_seeds)
        crawled_by_seed = dict.fromkeys(normalized_seeds, 0)
        per_seed_limit = max_pages // len(normalized_seeds) if normalized_seeds else 0

        def enqueue_links(links: list[str]) -> None:
            for link in links:
                normalized_link = self._normalize_url(link)
                for link_seed_url in normalized_seeds:
                    if self._belongs_to_seed(normalized_link, link_seed_url):
                        if normalized_link not in visited and normalized_link not in queued_urls:
                            frontier_by_seed[link_seed_url].append(normalized_link)
                            queued_urls.add(normalized_link)
                        break

        new_count = 0
        changed_count = 0
        unchanged_count = 0
        queued_count = 0
        errors: list[dict[str, str]] = []

        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            for seed_url in normalized_seeds:
                visited.add(seed_url)

                try:
                    response = client.get(seed_url)
                    response.raise_for_status()
                except Exception as exc:  # noqa: BLE001
                    errors.append({"url": seed_url, "error": str(exc)})
                    continue

                _, _, links = extract_page_data(response.text, seed_url, allowed_domains)
                enqueue_links(links)

            while normalized_seeds and all(
                crawled_by_seed[seed_url] < per_seed_limit
                for seed_url in normalized_seeds
            ):
                candidates: dict[str, str] = {}

                for seed_url in normalized_seeds:
                    queue = frontier_by_seed[seed_url]
                    while queue and queue[0] in visited:
                        queue.popleft()

                    if not queue:
                        candidates = {}
                        break

                    candidates[seed_url] = queue.popleft()

                if len(candidates) != len(normalized_seeds):
                    break

                round_pages: list[tuple[str, str, str, str, str, list[str]]] = []
                failed_url: str | None = None

                for seed_url, url in candidates.items():
                    try:
                        response = client.get(url)
                        response.raise_for_status()
                    except Exception as exc:  # noqa: BLE001
                        failed_url = url
                        errors.append({"url": url, "error": str(exc)})
                        break

                    title, text, links = extract_page_data(
                        response.text, url, allowed_domains
                    )

                    page_hash = self._hash_text(text)

                    previous = self.storage.get_page(url)
                    if previous is None:
                        status = "new"
                    elif previous["content_hash"] != page_hash:
                        status = "changed"
                    else:
                        status = "unchanged"

                    round_pages.append((seed_url, url, page_hash, status, title, links))

                if failed_url is not None:
                    visited.add(failed_url)
                    for seed_url, url in reversed(list(candidates.items())):
                        if url != failed_url:
                            frontier_by_seed[seed_url].appendleft(url)
                    continue

                for seed_url, url, page_hash, status, title, links in round_pages:
                    visited.add(url)
                    enqueue_links(links)
                    self.storage.upsert_page(url=url, content_hash=page_hash, status=status)
                    crawled_by_seed[seed_url] += 1
                    if status == "new":
                        new_count += 1
                    elif status == "changed":
                        changed_count += 1
                    else:
                        unchanged_count += 1

                    if status in {"new", "changed"}:
                        payload = {
                            "url": url,
                            "content_hash": page_hash,
                            "event": "page_updated",
                            "title": title,
                            "source_type": self._source_type_from_seed(seed_url),
                        }
                        self.publisher.publish(payload)
                        self.storage.set_status(url, "queued")
                        queued_count += 1

        return CrawlResult(
            crawled=sum(crawled_by_seed.values()),
            new=new_count,
            changed=changed_count,
            unchanged=unchanged_count,
            queued=queued_count,
            errors=errors,
        )
