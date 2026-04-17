from typing import List, Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class Source(BaseModel):
    title: str
    url: str
    source_type: str = "unknown"
    section: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
