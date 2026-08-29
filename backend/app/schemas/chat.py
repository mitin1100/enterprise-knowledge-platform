from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.retrieval import RetrievalLevel
from app.utils.enum import MessageRole


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str | None = None
    chunk_index: int
    page_number: int | None = None
    score: float


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    citations: list[Citation]
    created_at: datetime


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    retrieval_level: RetrievalLevel = RetrievalLevel.HYBRID_RERANKED
    top_k: int | None = Field(default=None, ge=1, le=50)


class ChatResponse(BaseModel):
    conversation_id: UUID
    user_message: MessageResponse
    assistant_message: MessageResponse
