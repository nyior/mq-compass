# Retrieval Service

A simple FastAPI retrieval service for the online question-answer side of a RAG demo.

It receives a question, retrieves relevant chunks from Pinecone, and asks OpenAI to generate a grounded answer using only that context.

## Project structure

```text
retrieval_service/
  main.py
  retrieval.py
  llm.py
  models.py
  config.py
  .env.example
  requirements.txt
  readme.md
```

## What this service does

- `POST /ask`: accepts a question and returns `{ answer, sources }`.
- `GET /health`: basic health check.
- Uses **the same embedding model name** as ingestion (`OPENAI_EMBEDDING_MODEL`) so query/doc vectors stay compatible.
- Retrieves top-k chunks from Pinecone.
- Generates a grounded answer with OpenAI.
- Deduplicates and returns source metadata (`title`, `url`, `source_type`).

## What this service does NOT do

- Crawling pages
- Queue consumption
- Chunking documents
- Ingestion upserts to Pinecone

## Setup

### 1) Install dependencies

From repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r retrieval_service/requirements.txt
```

### 2) Configure environment variables

This service uses `python-dotenv`, so local configuration can live in a `.env`
file instead of being exported in every terminal session.

Create a service-local `.env` file from the example:

```bash
cp retrieval_service/.env.example retrieval_service/.env
```

Then edit `retrieval_service/.env`.

Required:

```dotenv
OPENAI_API_KEY=your-openai-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=your-index-name
```

Optional (defaults shown):

```dotenv
PINECONE_NAMESPACE=mq-compass-demo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
RETRIEVAL_TOP_K=4
```

> Important: `OPENAI_EMBEDDING_MODEL` should match ingestion service settings.

The `.env` file is ignored by git so local credentials are not committed. Existing
shell environment variables still work, and take precedence over values loaded
from `.env`.

### 3) Run the API

```bash
uvicorn retrieval_service.main:app --reload --port 8103
```

## Test the API

### Swagger UI (/docs)

1. Open: `http://127.0.0.1:8103/docs`
2. Expand `POST /ask`
3. Click **Try it out**
4. Use body:

```json
{
  "question": "Why are messages piling up?"
}
```

5. Click **Execute** and inspect the JSON response.