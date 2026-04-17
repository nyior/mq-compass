import logging

from config import load_settings
from consumer import QueueConsumer
from documents import DocumentBuilder
from parser import fetch_and_parse_page
from storage import PageStorage
from vector_store import VectorStoreClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


class IngestionWorker:
    def __init__(self) -> None:
        settings = load_settings()
        self.storage = PageStorage(settings.sqlite_path)
        self.doc_builder = DocumentBuilder(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.vector_store = VectorStoreClient(
            index_name=settings.pinecone_index_name,
            namespace=settings.pinecone_namespace,
            embedding_model=settings.openai_embedding_model,
        )
        self.timeout_seconds = settings.http_timeout_seconds
        self.consumer = QueueConsumer(
            amqp_url=settings.amqp_url,
            queue_name=settings.queue_name,
        )

    def process_message(self, message: dict) -> None:
        url = message["url"]
        message_content_hash = message.get("content_hash", "")
        event = message.get("event", "")

        logger.info("Received event=%s url=%s", event, url)

        try:
            page = fetch_and_parse_page(url=url, timeout_seconds=self.timeout_seconds)

            if message_content_hash and message_content_hash != page.normalized_text_hash:
                logger.warning(
                    "Content hash mismatch for %s (msg=%s page=%s). Continuing for demo.",
                    url,
                    message_content_hash,
                    page.normalized_text_hash,
                )

            chunks = self.doc_builder.build_chunks(page)
            self.vector_store.upsert_page_chunks(page_url=url, chunks=chunks)
            self.storage.update_page_status(
                url=url,
                content_hash=message_content_hash or page.normalized_text_hash,
                status="indexed",
            )
            logger.info("Indexed %s (%d chunks)", url, len(chunks))
        except Exception:
            self.storage.update_page_status(
                url=url,
                content_hash=message_content_hash,
                status="failed",
            )
            raise

    def run(self) -> None:
        self.consumer.consume_forever(self.process_message)


if __name__ == "__main__":
    worker = IngestionWorker()
    worker.run()
