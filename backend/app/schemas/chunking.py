from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChunkingResult(BaseModel):
    document_id: UUID
    chunk_count: int
    embedding_model: str
    embedding_dimensions: int


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    page_number: int | None
    token_count: int
    embedding_id: str | None
    chunk_metadata: dict[str, Any] | None
    created_at: datetime


class ChunkListResponse(BaseModel):
    items: list[ChunkResponse]
    total: int


class ChunkContextResponse(BaseModel):
    document_id: UUID
    document_name: str
    chunk: ChunkResponse
    previous: ChunkResponse | None = None
    next: ChunkResponse | None = None


class ChunkingTriggerResponse(BaseModel):
    document_id: UUID
    status: str
