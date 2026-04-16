from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class PageStorage:
    def __init__(self, db_path: str = "crawler.db") -> None:
        self.db_path = Path(db_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pages (
                    url TEXT PRIMARY KEY,
                    content_hash TEXT,
                    last_crawled_at TEXT,
                    status TEXT
                )
                """
            )

    def get_page(self, url: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM pages WHERE url = ?", (url,)).fetchone()
            return dict(row) if row else None

    def upsert_page(self, url: str, content_hash: str, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pages (url, content_hash, last_crawled_at, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    last_crawled_at = excluded.last_crawled_at,
                    status = excluded.status
                """,
                (url, content_hash, now, status),
            )

    def set_status(self, url: str, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE pages SET status = ?, last_crawled_at = ? WHERE url = ?",
                (status, now, url),
            )

    def list_pages(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT url, content_hash, last_crawled_at, status FROM pages ORDER BY last_crawled_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]

    def stats(self) -> dict[str, int]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) AS c FROM pages").fetchone()["c"]
            rows = conn.execute(
                "SELECT status, COUNT(*) AS c FROM pages GROUP BY status"
            ).fetchall()

        counters = {"new": 0, "changed": 0, "unchanged": 0, "queued": 0}
        for row in rows:
            status = row["status"]
            if status in counters:
                counters[status] = row["c"]

        return {"total": total, **counters}
