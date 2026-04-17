from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .config import Settings

PROMPT_TEMPLATE = """You are a helpful support assistant for message queue users.
Answer the question using ONLY the context below.

Rules:
- If the context does not contain enough information, say you are not sure based on available docs.
- Do not invent facts or hidden configuration details.
- Keep the answer concise and practical.
- Where relevant, include debugging checks and next steps.

Question:
{question}

Context:
{context}
"""


class AnswerGenerator:
    def __init__(self, settings: Settings) -> None:
        self.prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        self.llm = ChatOpenAI(model=settings.openai_chat_model, api_key=settings.openai_api_key)

    def generate(self, question: str, context: str) -> str:
        chain = self.prompt | self.llm
        response = chain.invoke({"question": question, "context": context})
        return response.content.strip()
