from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field


class RetrievalLevel(IntEnum):
    VECTOR_ONLY = 1
    HYBRID = 2
    HYBRID_RERANKED = 3


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    level: RetrievalLevel = RetrievalLevel.VECTOR_ONLY
    top_k: int | None = Field(default=None, ge=1, le=50)


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    page_number: int | None
    score: float
    vector_score: float | None = None
    bm25_score: float | None = None
    rerank_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalResponse(BaseModel):
    query: str
    level: RetrievalLevel
    results: list[RetrievedChunk]
