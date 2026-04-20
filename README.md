# MQ Compass

MQ Compass is a beginner-friendly RAG demo with four independent services:
- `crawler` (FastAPI)
- `ingestion_worker` (queue consumer)
- `retrieval_service` (FastAPI)
- `web_widget` (static frontend + tiny proxy)

One-line mental model: **crawler discovers updates, ingestion indexes them, retrieval answers questions, widget calls retrieval**.

## Setting up the cloud resources (required first)

Before running anything, create/get these external services and credentials:
- CloudAMQP (for queueing)
- Pinecone (for vector storage)
- OpenAI (for embeddings + answer generation)



## Run locally (multi-terminal)

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

### Clone the repo and set your environment variables
```bash
git clone https://github.com/nyior/mq-compass.git
cd mq-compass
```
Next, each service expects its own .env file. This is important for the multi-terminal 
setup, since every service runs independently and reads its own configuration.

Create a `.env` file inside each of the following directories:

```bash
crawler/
ingestion_service/
retrieval_service/
```

The Crawlers’s `.env` file should contain:
```bash
AMQP_URL=amqpsxxxxx
CRAWLER_SAFETY_TIMEOUT_SECONDS=36000
```

The Ingestion service’s `.env` file should contain:
```bash
AMQP_URL=amqpsxxx
INGESTION_QUEUE=ingestion_jobs
SQLITE_PATH=crawler.db
OPENAI_API_KEY=sk-proj-xxxx
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
PINECONE_API_KEY=xxx
PINECONE_INDEX_NAME=lavinmq-docs
PINECONE_NAMESPACE=mq-compass-demo
HTTP_TIMEOUT_SECONDS=20
CHUNK_SIZE=900
CHUNK_OVERLAP=120
```

The Retrieval service’s `.env` file should contain:

```bash
PINECONE_API_KEY=xxx
PINECONE_INDEX_NAME=lavinmq-docs
PINECONE_NAMESPACE=mq-compass-demo
OPENAI_API_KEY=xxx
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
RETRIEVAL_TOP_K=4
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
