# Crawler Service

The crawler is a simple watcher service for the MQ Compass RAG demo.

Mental model: **crawl pages, detect changes, and send reprocess jobs to LavinMQ.**

It does **not** chunk data, generate embeddings, or call an LLM.

## What it does

- Crawls docs/blog pages from LavinMQ seed URLs using BFS.
- Extracts title + body text from HTML.
- Hashes content with SHA-256 to detect `new`, `changed`, and `unchanged` pages.
- Stores page metadata in SQLite.
- Publishes `page_updated` jobs to LavinMQ (CloudAMQP) for `new` and `changed` pages.
- Marks queued pages with status `queued`.

## Project layout

```text
crawler/
  main.py
  crawler.py
  parser.py
  storage.py
  queue.py
  requirements.txt
  readme.md
```

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r crawler/requirements.txt
```

## Configure CloudAMQP / LavinMQ

Set your AMQP connection string:

```bash
export AMQP_URL="amqps://<user>:<password>@<host>/<vhost>"
```

Optional settings:

```bash
export QUEUE_NAME="ingestion_jobs"
export CRAWLER_DB_PATH="crawler.db"
```

## Run the API

```bash
uvicorn crawler.main:app --reload --port 8101
```

## Use the API

Run one crawl:

```bash
curl -X POST "http://127.0.0.1:8101/crawl?max_pages=30"
```

List stored pages:

```bash
curl "http://127.0.0.1:8101/pages"
```

View stats:

```bash
curl "http://127.0.0.1:8101/stats"
```

## Message format

Published messages look like:

```json
{
  "url": "https://lavinmq.com/blog",
  "content_hash": "<sha256>",
  "event": "page_updated",
  "title": "LavinMQ blog"
}
```
