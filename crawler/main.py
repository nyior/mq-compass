from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from .crawler import SimpleCrawler
from .queue import QueuePublisher
from .storage import PageStorage


load_dotenv()

APP_TITLE = "MQ Compass Crawler"
DB_PATH = os.getenv("CRAWLER_DB_PATH", "crawler.db")
QUEUE_NAME = os.getenv("QUEUE_NAME", "ingestion_jobs")

app = FastAPI(
    title=APP_TITLE,
    description="Crawls LavinMQ docs/blog pages, tracks content changes, and queues updates.",
    version="0.1.0",
    docs_url="/doc",
)

storage = PageStorage(db_path=DB_PATH)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "crawler"}


@app.post("/crawl")
def crawl_once(max_pages: int = 50) -> dict:
    amqp_url = os.getenv("AMQP_URL")
    if not amqp_url:
        raise HTTPException(
            status_code=500,
            detail="AMQP_URL is not configured",
        )

    publisher = QueuePublisher(amqp_url=amqp_url, queue_name=QUEUE_NAME)
    crawler = SimpleCrawler(storage=storage, publisher=publisher)
    result = crawler.run(max_pages=max_pages)
    return {
        "service": "crawler",
        "result": {
            "crawled": result.crawled,
            "new": result.new,
            "changed": result.changed,
            "unchanged": result.unchanged,
            "queued": result.queued,
            "errors": result.errors,
        },
    }


@app.get("/pages")
def pages() -> dict:
    return {"pages": storage.list_pages()}


@app.get("/stats")
def stats() -> dict:
    return storage.stats()
