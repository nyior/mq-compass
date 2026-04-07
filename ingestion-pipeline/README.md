# Ingestion Pipeline

This FastAPI service models the ingestion worker API.

It accepts harvested source jobs, produces simple chunks and placeholder embeddings,
and returns a Pinecone-oriented record shape.
