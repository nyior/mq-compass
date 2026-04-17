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

Required:

```bash
export OPENAI_API_KEY="your-openai-key"
export PINECONE_API_KEY="your-pinecone-key"
export PINECONE_INDEX_NAME="your-index-name"
```

Optional (defaults shown):

```bash
export PINECONE_NAMESPACE="mq-compass-demo"
export OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
export OPENAI_CHAT_MODEL="gpt-4o-mini"
export RETRIEVAL_TOP_K="4"
```

> Important: `OPENAI_EMBEDDING_MODEL` should match ingestion service settings.

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

### cURL example

```bash
curl -X POST "http://127.0.0.1:8103/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Why are messages piling up?"}'
```

Expected shape:

```json
{
  "answer": "...",
  "sources": [
    {
      "title": "Consumers",
      "url": "https://example.com/docs/consumers",
      "source_type": "docs",
      "section": "Acknowledgements"
    }
  ]
}
```
