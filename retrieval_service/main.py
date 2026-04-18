import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .llm import AnswerGenerator
from .models import AskRequest, AskResponse
from .retrieval import Retriever, build_sources, format_context


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("retrieval_service")

app = FastAPI(
    title="MQ Compass Retrieval Service",
    description="Simple RAG retrieval and answer generation API",
    version="0.1.0",
)

# Strong discourage wildcards in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup() -> None:
    settings = Settings.from_env()
    app.state.settings = settings
    app.state.retriever = Retriever(settings)
    app.state.answer_generator = AnswerGenerator(settings)
    logger.info(
        "Service started. index=%s namespace=%s embedding_model=%s top_k=%s",
        settings.pinecone_index_name,
        settings.pinecone_namespace,
        settings.openai_embedding_model,
        settings.top_k,
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "retrieval_service"}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    question = payload.question.strip()
    logger.info("Incoming question: %s", question)

    try:
        chunks = app.state.retriever.get_relevant_chunks(question)
        logger.info("Retrieved chunks: %s", len(chunks))

        sources = build_sources(chunks)
        logger.info("Selected source urls: %s", [source.url for source in sources])

        if not chunks:
            logger.warning("No context retrieved. Returning safe fallback response.")
            return AskResponse(
                answer=(
                    "I’m not sure based on the available context. "
                    "Please review the linked sources or ask a more specific question."
                ),
                sources=sources,
            )

        context = format_context(chunks)
        answer = app.state.answer_generator.generate(question=question, context=context)
        logger.info("Answer generation succeeded")
        return AskResponse(answer=answer, sources=sources)

    except Exception:
        logger.exception("Answer generation failed")
        raise HTTPException(status_code=500, detail="Failed to process question")
