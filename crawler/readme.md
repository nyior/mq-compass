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

Create a repository-root `.env` file and add your CloudAMQP connection string:

```dotenv
AMQP_URL=amqps://<user>:<password>@<host>/<vhost>
```

Optional settings:

```dotenv
QUEUE_NAME=ingestion_jobs
CRAWLER_DB_PATH=crawler.db
CRAWLER_SAFETY_TIMEOUT_SECONDS=3600
```

`CRAWLER_SAFETY_TIMEOUT_SECONDS` is the maximum runtime for one crawl request.
It defaults to `3600` seconds, or 60 minutes.

The `.env` file is loaded automatically when `crawler.main` 
starts and is ignored by git so credentials are not committed.

## Run the API

```bash
uvicorn crawler.main:app --reload --port 8101
```

## Test the API
Open the API docs UI:

```text
http://127.0.0.1:8101/doc
```

Use **Try it out** and **Execute** in the docs page to test:

- `GET /health` - check the service is running.
- `POST /crawl` - run one crawl. Omit `max_pages` to crawl all reachable seed pages, or set a limit such as `30`. Crawls stop after `CRAWLER_SAFETY_TIMEOUT_SECONDS`.
- `GET /pages` - list pages stored in SQLite.
- `GET /stats` - view crawl/storage totals.

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
