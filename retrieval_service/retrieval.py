from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from .config import Settings
from .models import Source


logger = logging.getLogger(__name__)

MIN_USEFUL_CONTEXT_CHARS = 120
MIN_RELEVANCE_SCORE = 0.58
MAX_SOURCES = 3
BOILERPLATE_SECTION_HEADINGS = {
    "Help and feedback",
    "Managed LavinMQ instance via CloudAMQP",
    "More resources on consumers",
}


@dataclass
class RetrievedChunk:
    document: Document
    score: float


def _section(metadata: dict) -> str:
    return (
        metadata.get("section")
        or metadata.get("heading")
        or metadata.get("section_heading")
        or ""
    )


def _is_useful_context(document: Document) -> bool:
    text = " ".join((document.page_content or "").split())
    if _section(document.metadata or {}) in BOILERPLATE_SECTION_HEADINGS:
        return False
    if len(text) < MIN_USEFUL_CONTEXT_CHARS:
        return False
    if text.startswith("For more information"):
        return False

    return (
        "Documentation menu:" not in text
        and "prettier-ignore" not in text
        and "Managed LavinMQ instance via CloudAMQP" not in text
    )


class Retriever:
    def __init__(self, settings: Settings) -> None:
        embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )

        self.vector_store = PineconeVectorStore(
            index_name=settings.pinecone_index_name,
            embedding=embeddings,
            namespace=settings.pinecone_namespace,
            pinecone_api_key=settings.pinecone_api_key,
        )
        self.top_k = settings.top_k

    def get_relevant_chunks(self, question: str) -> List[RetrievedChunk]:
        candidate_k = max(self.top_k * 3, 10)
        results = self.vector_store.similarity_search_with_score(question, k=candidate_k)
        useful_results: list[RetrievedChunk] = []

        for document, score in results:
            metadata = document.metadata or {}
            text = " ".join((document.page_content or "").split())
            logger.info(
                "Candidate chunk score=%.4f chars=%s url=%s section=%s preview=%s",
                score,
                len(text),
                metadata.get("url") or metadata.get("source_url"),
                _section(metadata),
                text[:160],
            )

            if score >= MIN_RELEVANCE_SCORE and _is_useful_context(document):
                useful_results.append(RetrievedChunk(document=document, score=score))

        return useful_results[: self.top_k]


def build_sources(chunks: List[RetrievedChunk]) -> List[Source]:
    """Extract and deduplicate source metadata for UI rendering."""

    deduped: dict[str, Source] = {}
    for chunk in chunks:
        metadata = chunk.document.metadata or {}
        url = metadata.get("url") or metadata.get("source_url")
        if not url:
            continue

        if url in deduped:
            continue

        deduped[url] = Source(
            title=metadata.get("title") or metadata.get("page_title") or "Untitled source",
            url=url,
            source_type=metadata.get("source_type", "unknown"),
            section=_section(metadata) or None,
        )

    return list(deduped.values())[:MAX_SOURCES]


def format_context(chunks: List[RetrievedChunk]) -> str:
    """Create a readable context block for prompt grounding."""

    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        document = chunk.document
        metadata = document.metadata or {}
        title = metadata.get("title") or metadata.get("page_title") or "Untitled"
        url = metadata.get("url") or metadata.get("source_url") or "unknown"
        section = _section(metadata)
        section_line = f"Section: {section}\n" if section else ""

        parts.append(
            f"[{i}] Title: {title}\n"
            f"URL: {url}\n"
            f"{section_line}"
            f"Content:\n{document.page_content.strip()}"
        )

    return "\n\n".join(parts)
