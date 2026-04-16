import hashlib
from typing import List

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore


class VectorStoreClient:
    def __init__(self, index_name: str, namespace: str, embedding_model: str) -> None:
        embeddings = OpenAIEmbeddings(model=embedding_model)
        self.store = PineconeVectorStore(
            index_name=index_name,
            embedding=embeddings,
            namespace=namespace,
        )

    def upsert_page_chunks(self, page_url: str, chunks: List[Document]) -> None:
        url_hash = hashlib.sha256(page_url.encode("utf-8")).hexdigest()[:16]
        ids = [f"{url_hash}-{chunk.metadata['chunk_index']}" for chunk in chunks]
        self.store.add_documents(documents=chunks, ids=ids)
