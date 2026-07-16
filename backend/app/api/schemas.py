from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    candidate_name: str
    page: int
    excerpt: str


class AnswerResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]


class ConversationResponse(BaseModel):
    id: UUID


class ConversationSummaryResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationsResponse(BaseModel):
    conversations: list[ConversationSummaryResponse]


class MessageResponse(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    sources: list[SourceResponse]
    created_at: datetime


class MessagesResponse(BaseModel):
    messages: list[MessageResponse]
