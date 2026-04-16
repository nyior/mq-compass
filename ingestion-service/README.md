# RAG Ingestion Worker (Queue + LangChain + Pinecone)

This worker is a simple background ingestion processor for the demo RAG stack.

Mental model:

> Pick up a `page_updated` job, fetch that page, split into section-aware chunks, embed chunks, upsert to Pinecone, mark SQLite status.

## Files

- `main.py` - wiring + message processing flow
- `consumer.py` - LavinMQ/CloudAMQP consumer with manual ack
- `parser.py` - URL fetch + title/main-content extraction + hash generation
- `documents.py` - HTML heading split + recursive chunk split
- `vector_store.py` - embeddings + Pinecone upsert
- `storage.py` - SQLite status updates
- `config.py` - environment-based configuration

## Install

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r worker/requirements.txt
```

## Configure

Create `.env` in the repo root:

```env
# CloudAMQP / LavinMQ
AMQP_URL=amqps://USER:PASSWORD@HOST/VHOST
INGESTION_QUEUE=ingestion_jobs

# SQLite used by crawler + worker
SQLITE_PATH=crawler.db

# OpenAI embeddings
OPENAI_API_KEY=your-openai-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Pinecone
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=your-index-name
PINECONE_NAMESPACE=mq-compass-demo

# Optional tuning
HTTP_TIMEOUT_SECONDS=20
CHUNK_SIZE=900
CHUNK_OVERLAP=120
```

## Run

From the repo root:

```bash
python -m worker.main
```

The worker will:

1. Connect to `ingestion_jobs` and consume one message at a time.
2. For each message:
   - fetch page HTML from `url`
   - extract title + main content HTML
   - compute normalized text hash and compare with message `content_hash`
   - split by HTML headings (`h1`, `h2`, `h3`)
   - recursively split oversized sections
   - embed and upsert chunks into Pinecone with metadata
   - update SQLite `pages.status` to `indexed`
3. Acknowledge only after successful processing.

If processing fails, the worker sets SQLite status to `failed` and leaves the message unacked.

## Expected message format

```json
{
  "url": "https://example.com/documentation/queues",
  "content_hash": "abc123",
  "event": "page_updated"
}
```
