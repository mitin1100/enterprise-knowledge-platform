from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.workspace import Workspace


class EvaluationRun(BaseModel, table=True):
    """
    A single evaluation pass of a dataset against the RAG pipeline, with
    the aggregate metrics shown on the evaluation dashboard summary.
    """

    __tablename__ = "evaluation_run"

    id: UUID = Field(
        sa_column=Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            default=uuid4,
        ),
        description="Unique identifier for the evaluation run",
    )

    workspace_id: UUID = Field(
        sa_column=Column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey("workspace.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        description="ID of the workspace this run was executed against",
    )

    created_by: UUID = Field(
        sa_column=Column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        description="ID of the user who launched this evaluation run",
    )

    name: Optional[str] = Field(
        default=None,
        sa_type=String(255),
        description="Optional label for the run",
    )

    retrieval_level: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="RetrievalLevel used for this run",
    )

    pass_threshold: float = Field(
        sa_column=Column(Float, nullable=False),
        description="Composite score threshold used to mark items pass/fail",
    )

    item_count: int = Field(sa_column=Column(Integer, nullable=False))
    passed_count: int = Field(sa_column=Column(Integer, nullable=False))

    avg_retrieval_precision: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
    )
    avg_context_relevance: float = Field(sa_column=Column(Float, nullable=False))
    avg_answer_faithfulness: float = Field(sa_column=Column(Float, nullable=False))
    avg_answer_relevancy: float = Field(sa_column=Column(Float, nullable=False))
    hallucination_rate: float = Field(sa_column=Column(Float, nullable=False))
    avg_latency_ms: float = Field(sa_column=Column(Float, nullable=False))

    total_prompt_tokens: int = Field(sa_column=Column(Integer, nullable=False))
    total_completion_tokens: int = Field(sa_column=Column(Integer, nullable=False))
    total_tokens: int = Field(sa_column=Column(Integer, nullable=False))

    @property
    def pass_rate(self) -> float:
        return self.passed_count / self.item_count if self.item_count else 0.0

    workspace: "Workspace" = Relationship()

    items: list["EvaluationItem"] = Relationship(
        back_populates="run",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
            "order_by": "EvaluationItem.created_at",
        },
    )


class EvaluationItem(BaseModel, table=True):
    """
    Per-question result of an evaluation run: what was retrieved, what
    was generated, and the scored metrics — the row data behind the
    evaluation dashboard table.
    """

    __tablename__ = "evaluation_item"

    id: UUID = Field(
        sa_column=Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            default=uuid4,
        ),
        description="Unique identifier for the evaluation item",
    )

    run_id: UUID = Field(
        sa_column=Column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey("evaluation_run.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        description="ID of the parent evaluation run",
    )

    question: str = Field(sa_type=Text, nullable=False)
    expected_answer: str = Field(sa_type=Text, nullable=False)
    expected_source: list = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, default=list),
    )

    generated_answer: str = Field(sa_type=Text, nullable=False)
    retrieved_chunks: list = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, default=list),
        description="Snapshot of the retrieved chunks shown on the dashboard",
    )

    retrieval_precision: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
    )
    context_relevance: float = Field(sa_column=Column(Float, nullable=False))
    answer_faithfulness: float = Field(sa_column=Column(Float, nullable=False))
    answer_relevancy: float = Field(sa_column=Column(Float, nullable=False))
    hallucinated: bool = Field(sa_column=Column(Boolean, nullable=False))
    judge_reasoning: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    retrieval_latency_ms: float = Field(sa_column=Column(Float, nullable=False))
    generation_latency_ms: float = Field(sa_column=Column(Float, nullable=False))
    total_latency_ms: float = Field(sa_column=Column(Float, nullable=False))

    prompt_tokens: int = Field(sa_column=Column(Integer, nullable=False))
    completion_tokens: int = Field(sa_column=Column(Integer, nullable=False))
    tokens_estimated: bool = Field(sa_column=Column(Boolean, nullable=False))

    score: float = Field(sa_column=Column(Float, nullable=False))
    passed: bool = Field(sa_column=Column(Boolean, nullable=False))
    error_message: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    run: "EvaluationRun" = Relationship(back_populates="items")
