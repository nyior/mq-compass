from __future__ import annotations

from typing import List

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from .config import Settings
from .models import Source


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

    def get_relevant_chunks(self, question: str) -> List[Document]:
        return self.vector_store.similarity_search(question, k=self.top_k)


def build_sources(chunks: List[Document]) -> List[Source]:
    """Extract and deduplicate source metadata for UI rendering."""

    deduped: dict[str, Source] = {}
    for chunk in chunks:
        metadata = chunk.metadata or {}
        url = metadata.get("url") or metadata.get("source_url")
        if not url:
            continue

        if url in deduped:
            continue

        deduped[url] = Source(
            title=metadata.get("title") or metadata.get("page_title") or "Untitled source",
            url=url,
            source_type=metadata.get("source_type", "unknown"),
            section=metadata.get("section") or metadata.get("heading"),
        )

    return list(deduped.values())


def format_context(chunks: List[Document]) -> str:
    """Create a readable context block for prompt grounding."""

    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        metadata = chunk.metadata or {}
        title = metadata.get("title") or metadata.get("page_title") or "Untitled"
        url = metadata.get("url") or metadata.get("source_url") or "unknown"
        section = metadata.get("section") or metadata.get("heading") or ""
        section_line = f"Section: {section}\n" if section else ""

        parts.append(
            f"[{i}] Title: {title}\n"
            f"URL: {url}\n"
            f"{section_line}"
            f"Content:\n{chunk.page_content.strip()}"
        )

    return "\n\n".join(parts)
