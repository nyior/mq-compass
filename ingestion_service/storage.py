from pathlib import Path
import sqlite3


class PageStorage:
    def __init__(self, sqlite_path: str) -> None:
        self.sqlite_path = sqlite_path
        Path(self.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
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
            conn.commit()

    def update_page_status(self, url: str, content_hash: str, status: str) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                """
                INSERT INTO pages (url, content_hash, status)
                VALUES (?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                  content_hash=excluded.content_hash,
                  status=excluded.status
                """,
                (url, content_hash, status),
            )
            conn.commit()
