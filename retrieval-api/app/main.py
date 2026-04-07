from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(
    title="MQ Compass Retrieval API",
    description="Retrieves relevant knowledge chunks and returns assistant responses.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3)


class ContextChunk(BaseModel):
    title: str
    snippet: str


def build_context(question: str) -> List[ContextChunk]:
    troubleshooting_terms = [
        "error",
        "stuck",
        "fail",
        "backing up",
        "backlog",
        "slow",
        "delayed",
        "retry",
    ]
    topic = "troubleshooting" if any(term in question.lower() for term in troubleshooting_terms) else "learning"
    return [
        ContextChunk(
            title="LavinMQ Overview",
            snippet="LavinMQ is a message broker compatible with AMQP concepts and is commonly used for asynchronous workloads.",
        ),
        ContextChunk(
            title="What To Check First",
            snippet=f"For {topic} questions, start with queue depth, consumer availability, connection health, and recent deploy changes.",
        ),
    ]


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok", "service": "retrieval-api"}


@app.post("/ask")
def ask(payload: QuestionRequest) -> dict:
    context = build_context(payload.question)
    answer = (
        "Start by identifying whether you are learning the workflow or debugging a failure. "
        "For LavinMQ issues, verify producers can publish, consumers are connected, and queue metrics look normal."
    )
    return {
        "service": "retrieval-api",
        "question": payload.question,
        "answer": answer,
        "sources": [chunk.model_dump() for chunk in context],
    }
