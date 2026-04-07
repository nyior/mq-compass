from datetime import datetime, timezone
from typing import List, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(
    title="MQ Compass Source Harvester",
    description="Collects knowledge from product and support sources and prepares jobs for LavinMQ.",
    version="0.1.0",
)


class SourceConfig(BaseModel):
    name: str
    kind: Literal["docs", "blog", "forum", "support_ticket", "internal_doc"]
    uri: str


class HarvestRequest(BaseModel):
    sources: List[SourceConfig] = Field(min_length=1)


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok", "service": "source-harvester"}


@app.post("/harvest")
def harvest_sources(payload: HarvestRequest) -> dict:
    jobs = [
        {
            "source_name": source.name,
            "source_kind": source.kind,
            "uri": source.uri,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued_for_ingestion",
            "broker": "lavinmq",
        }
        for source in payload.sources
    ]
    return {
        "service": "source-harvester",
        "job_count": len(jobs),
        "jobs": jobs,
    }
