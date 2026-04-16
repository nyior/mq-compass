import sqlite3


class PageStorage:
    def __init__(self, sqlite_path: str) -> None:
        self.sqlite_path = sqlite_path

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
