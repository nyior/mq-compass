from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter

try:
    from worker.parser import ParsedPage
except ModuleNotFoundError as exc:
    if exc.name != "worker":
        raise
    from parser import ParsedPage


MIN_USEFUL_CHUNK_CHARS = 120
BOILERPLATE_MARKERS = (
    "Documentation menu:",
    "prettier-ignore",
    "Managed LavinMQ instance via CloudAMQP",
)
BOILERPLATE_SECTION_HEADINGS = {
    "Help and feedback",
    "Managed LavinMQ instance via CloudAMQP",
    "More resources on consumers",
}


def _is_useful_chunk(chunk: Document) -> bool:
    text = " ".join(chunk.page_content.split())
    section_heading = (
        chunk.metadata.get("section_heading")
        or chunk.metadata.get("h3")
        or chunk.metadata.get("h2")
        or chunk.metadata.get("h1")
    )
    if section_heading in BOILERPLATE_SECTION_HEADINGS:
        return False
    if len(text) < MIN_USEFUL_CHUNK_CHARS:
        return False
    if text.startswith("For more information"):
        return False

    return not any(marker in text for marker in BOILERPLATE_MARKERS)


class DocumentBuilder:
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 120) -> None:
        self.section_splitter = HTMLHeaderTextSplitter(
            headers_to_split_on=[("h1", "h1"), ("h2", "h2"), ("h3", "h3")]
        )
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.chunk_size = chunk_size

    def build_chunks(self, page: ParsedPage) -> List[Document]:
        section_docs = self.section_splitter.split_text(page.main_html)
        if not section_docs:
            section_docs = [Document(page_content=page.main_text, metadata={})]

        enriched_sections: List[Document] = []
        for section in section_docs:
            metadata = {
                **section.metadata,
                "url": page.url,
                "title": page.title,
                "source_type": page.source_type,
            }
            section_heading = section.metadata.get("h3") or section.metadata.get("h2") or section.metadata.get("h1")
            if section_heading:
                metadata["section_heading"] = section_heading

            enriched_sections.append(
                Document(page_content=section.page_content.strip(), metadata=metadata)
            )

        final_chunks: List[Document] = []
        for section_doc in enriched_sections:
            if len(section_doc.page_content) <= self.chunk_size:
                if _is_useful_chunk(section_doc):
                    final_chunks.append(section_doc)
                continue

            split_docs = self.recursive_splitter.split_documents([section_doc])
            final_chunks.extend(chunk for chunk in split_docs if _is_useful_chunk(chunk))

        for index, chunk in enumerate(final_chunks):
            chunk.metadata["chunk_index"] = index
            chunk.metadata["chunk_text"] = chunk.page_content

        return final_chunks
