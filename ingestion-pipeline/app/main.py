from typing import List

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(
    title="MQ Compass Ingestion Pipeline",
    description="Chunks harvested content, creates embeddings, and prepares records for Pinecone.",
    version="0.1.0",
)


class IngestionJob(BaseModel):
    source_name: str
    source_kind: str
    uri: str
    text: str = Field(min_length=1)


class IngestionRequest(BaseModel):
    jobs: List[IngestionJob] = Field(min_length=1)


def chunk_text(text: str, size: int = 120) -> List[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [text]


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok", "service": "ingestion-pipeline"}


@app.post("/ingest")
def ingest(payload: IngestionRequest) -> dict:
    records = []
    for job in payload.jobs:
        for index, chunk in enumerate(chunk_text(job.text), start=1):
            records.append(
                {
                    "id": f"{job.source_name.lower().replace(' ', '-')}-{index}",
                    "metadata": {
                        "source_name": job.source_name,
                        "source_kind": job.source_kind,
                        "uri": job.uri,
                    },
                    "chunk": chunk,
                    "embedding_model": "demo-text-embedding-3-small",
                    "embedding_preview": [0.12, 0.34, 0.56],
                    "destination": "pinecone",
                }
            )
    return {
        "service": "ingestion-pipeline",
        "record_count": len(records),
        "records": records,
    }
