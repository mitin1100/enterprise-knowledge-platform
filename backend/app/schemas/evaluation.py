from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.retrieval import RetrievalLevel


class EvaluationDatasetItem(BaseModel):
    """
    One row of an evaluation dataset: a question, the answer it should
    produce, and which documents that answer should be grounded in.
    """

    question: str = Field(min_length=1, max_length=2000)
    expected_answer: str = Field(default="", max_length=4000)
    expected_source: list[str] = Field(default_factory=list)


class EvaluationDatasetParseResponse(BaseModel):
    items: list[EvaluationDatasetItem]


class EvaluationRunRequest(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    items: list[EvaluationDatasetItem] = Field(min_length=1, max_length=200)
    retrieval_level: RetrievalLevel = RetrievalLevel.HYBRID_RERANKED
    top_k: int | None = Field(default=None, ge=1, le=50)
    pass_threshold: float | None = Field(default=None, ge=0, le=1)


class RetrievedChunkResult(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str | None = None
    chunk_index: int
    page_number: int | None = None
    content_preview: str
    score: float


class TokenUsageResult(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated: bool


class LatencyResult(BaseModel):
    retrieval_ms: float
    generation_ms: float
    total_ms: float


class EvaluationItemResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    expected_answer: str
    expected_source: list[str]
    generated_answer: str
    retrieved_chunks: list[RetrievedChunkResult]
    retrieval_precision: float | None
    context_relevance: float
    answer_faithfulness: float
    answer_relevancy: float
    hallucinated: bool
    judge_reasoning: str | None
    latency: LatencyResult
    token_usage: TokenUsageResult
    score: float
    passed: bool
    error: str | None = None


class EvaluationRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str | None
    item_count: int
    passed_count: int
    pass_rate: float
    avg_retrieval_precision: float | None
    avg_context_relevance: float
    avg_answer_faithfulness: float
    avg_answer_relevancy: float
    hallucination_rate: float
    avg_latency_ms: float
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    created_at: datetime


class EvaluationRunResponse(EvaluationRunSummary):
    items: list[EvaluationItemResult]


class EvaluationRunListResponse(BaseModel):
    items: list[EvaluationRunSummary]
    total: int
