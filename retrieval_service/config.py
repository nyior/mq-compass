import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Environment configuration for the retrieval service."""

    openai_api_key: str = Field(min_length=1)
    pinecone_api_key: str = Field(min_length=1)
    pinecone_index_name: str = Field(min_length=1)
    pinecone_namespace: str = Field(default="mq-compass-demo")

    # Must match ingestion embedding model for semantic compatibility.
    openai_embedding_model: str = Field(default="text-embedding-3-small")

    openai_chat_model: str = Field(default="gpt-4o-mini")
    top_k: int = Field(default=4, ge=1, le=10)

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            pinecone_api_key=os.getenv("PINECONE_API_KEY", ""),
            pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", os.getenv("PINECONE_INDEX", "")),
            pinecone_namespace=os.getenv("PINECONE_NAMESPACE", "mq-compass-demo"),
            openai_embedding_model=os.getenv(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
            ),
            openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            top_k=int(os.getenv("RETRIEVAL_TOP_K", "4")),
        )
