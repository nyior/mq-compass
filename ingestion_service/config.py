from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass
class Settings:
    amqp_url: str
    queue_name: str
    sqlite_path: str
    pinecone_index_name: str
    pinecone_namespace: str
    openai_embedding_model: str
    # openai_embedding_dimensions: int
    http_timeout_seconds: float
    chunk_size: int
    chunk_overlap: int



def load_settings() -> Settings:
    load_dotenv()

    amqp_url = os.getenv("AMQP_URL")
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

    if not amqp_url:
        raise ValueError("AMQP_URL is required")
    if not pinecone_index_name:
        raise ValueError("PINECONE_INDEX_NAME is required")

    return Settings(
        amqp_url=amqp_url,
        queue_name=os.getenv("INGESTION_QUEUE", "ingestion_jobs"),
        sqlite_path=os.getenv("SQLITE_PATH", "crawler.db"),
        pinecone_index_name=pinecone_index_name,
        pinecone_namespace=os.getenv("PINECONE_NAMESPACE", "mq-compass-demo"),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        http_timeout_seconds=float(os.getenv("HTTP_TIMEOUT_SECONDS", "20")),
        chunk_size=int(os.getenv("CHUNK_SIZE", "900")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "120")),
    )
