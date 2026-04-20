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

GENERAL_PROMPT_TEMPLATE = """You are a helpful support assistant for message queue users.
No directly useful product documentation was found for this question in the retrieval database.

Rules:
- Start by saying that no directly useful product doc was found, so the answer is not grounded in the product docs in the database.
- Then answer using general message queue knowledge to the best of your ability.
- Do not claim that product-specific docs or configuration support something unless the context says so.
- Keep the answer concise and practical.
- Where relevant, include debugging checks and next steps.

Question:
{question}
"""


class AnswerGenerator:
    def __init__(self, settings: Settings) -> None:
        self.prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        self.general_prompt = ChatPromptTemplate.from_template(GENERAL_PROMPT_TEMPLATE)
        self.llm = ChatOpenAI(model=settings.openai_chat_model, api_key=settings.openai_api_key)

    def generate(self, question: str, context: str) -> str:
        chain = self.prompt | self.llm
        response = chain.invoke({"question": question, "context": context})
        return response.content.strip()

    def generate_general(self, question: str) -> str:
        chain = self.general_prompt | self.llm
        response = chain.invoke({"question": question})
        return response.content.strip()
