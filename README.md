# MQ Compass

MQ Compass is a beginner-friendly RAG demo with four independent services:
- `crawler` (FastAPI)
- `ingestion_worker` (queue consumer)
- `retrieval_service` (FastAPI)
- `web_widget` (static frontend + tiny proxy)

One-line mental model: **crawler discovers updates, ingestion indexes them, retrieval answers questions, widget calls retrieval**.

## 0) Cloud resources (required first)

Before running anything, create/get these external services and credentials:
- CloudAMQP (for queueing)
- Pinecone (for vector storage)
- OpenAI (for embeddings + answer generation)

Create a repo-root `.env` file:

```bash
cp .env.example .env
```

Fill at least:

```env
OPENAI_API_KEY=...
PINECONE_API_KEY=...
PINECONE_INDEX=...
AMQP_URL=amqps://<user>:<password>@<host>/<vhost>
BACKEND_API_URL=http://retrieval_service:8000
DATABASE_PATH=/data/crawler.db
```

Notes:
- In Docker, `BACKEND_API_URL` should stay `http://retrieval_service:8000` (service-to-service DNS).
- For local multi-terminal runs, export `BACKEND_API_URL=http://127.0.0.1:8000` before starting `web_widget`.
- `crawler` and `ingestion_worker` both use the same SQLite file path from `DATABASE_PATH`.

---

## 1) Run locally (multi-terminal)

### Install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r crawler/requirements.txt
pip install -r ingestion_service/requirements.txt
pip install -r retrieval_service/requirements.txt
```

```bash
cd chat_widget
npm install
cd ..
```

### Ingestion path (3 terminals)

Terminal A (worker):
```bash
source .venv/bin/activate
export DATABASE_PATH=./crawler.db
cd ingestion_service
PORT=8102 python server.py
```

Terminal B (crawler API):
```bash
source .venv/bin/activate
export DATABASE_PATH=./crawler.db
uvicorn crawler.main:app --reload --port 8001
```

Trigger crawl (Terminal C):
```bash
curl -X POST "http://127.0.0.1:8001/crawl"
```

(Or use Swagger at `http://127.0.0.1:8001/doc`.)

### Retrieval path (2 terminals)

Terminal D (retrieval API):
```bash
source .venv/bin/activate
uvicorn retrieval_service.main:app --reload --port 8000
```

Terminal E (web widget):
```bash
export BACKEND_API_URL=http://127.0.0.1:8000
cd chat_widget
PORT=3000 node server.js
```

Open:
- Crawler docs: `http://localhost:8001/doc`
- Retrieval API: `http://localhost:8000`
- Web widget: `http://localhost:3000`

---

## 2) Run with Docker (one command)

Docker is the easier way to run everything without opening multiple terminals.

```bash
docker-compose up --build
```

Open:
- crawler → `http://localhost:8001`
- retrieval API → `http://localhost:8000`
- web widget → `http://localhost:3000`

Trigger ingestion:
- Swagger: `http://localhost:8001/doc` → `POST /crawl`
- or terminal:

```bash
curl -X POST "http://localhost:8001/crawl"
```

### What Docker changes (and what it does not)

- Docker removes multi-terminal setup.
- Services are still independent.
- They still communicate through CloudAMQP, Pinecone, and HTTP.
- `crawler` + `ingestion_worker` share one SQLite file via Docker volume (`DATABASE_PATH=/data/crawler.db`).
