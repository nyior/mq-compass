# MQ Compass

MQ Compass is a demo RAG stack for a LavinMQ-focused docs assistant.

## Services

- `source-harvester`: fetches and normalizes knowledge from docs, blogs, forums, and internal support sources, then prepares jobs for LavinMQ.
- `ingestion-pipeline`: consumes harvested jobs, creates chunks and embeddings, and writes records to Pinecone.
- `retrieval-api`: receives user questions, retrieves relevant chunks, and returns an LLM-ready answer.
- `chat-widget`: a pluggable bottom-right chat widget for docs and blog pages.

## Quick start

### Python services

Create a virtual environment at the project root and install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run a service:

```bash
uvicorn app.main:app --reload --port 8101
```

Use the correct directory for each service.

### Chat widget

```bash
cd chat-widget
npm run dev
```

Open `http://127.0.0.1:8301`.
