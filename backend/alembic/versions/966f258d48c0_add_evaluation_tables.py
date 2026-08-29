"""add evaluation run and evaluation item tables

Revision ID: 966f258d48c0
Revises: a1f39d7c2b44
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "966f258d48c0"
down_revision: Union[str, Sequence[str], None] = "a1f39d7c2b44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "evaluation_run",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column(
            "name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column("retrieval_level", sa.Integer(), nullable=False),
        sa.Column("pass_threshold", sa.Float(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("passed_count", sa.Integer(), nullable=False),
        sa.Column("avg_retrieval_precision", sa.Float(), nullable=True),
        sa.Column("avg_context_relevance", sa.Float(), nullable=False),
        sa.Column("avg_answer_faithfulness", sa.Float(), nullable=False),
        sa.Column("avg_answer_relevancy", sa.Float(), nullable=False),
        sa.Column("hallucination_rate", sa.Float(), nullable=False),
        sa.Column("avg_latency_ms", sa.Float(), nullable=False),
        sa.Column("total_prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("total_completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.id"],
            name=op.f("fk_evaluation_run_workspace_id_workspace"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_evaluation_run_created_by_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_run")),
    )
    op.create_index(
        op.f("ix_evaluation_run_workspace_id"),
        "evaluation_run",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evaluation_run_created_by"),
        "evaluation_run",
        ["created_by"],
        unique=False,
    )

    op.create_table(
        "evaluation_item",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=False),
        sa.Column("expected_source", sa.JSON(), nullable=False),
        sa.Column("generated_answer", sa.Text(), nullable=False),
        sa.Column("retrieved_chunks", sa.JSON(), nullable=False),
        sa.Column("retrieval_precision", sa.Float(), nullable=True),
        sa.Column("context_relevance", sa.Float(), nullable=False),
        sa.Column("answer_faithfulness", sa.Float(), nullable=False),
        sa.Column("answer_relevancy", sa.Float(), nullable=False),
        sa.Column("hallucinated", sa.Boolean(), nullable=False),
        sa.Column("judge_reasoning", sa.Text(), nullable=True),
        sa.Column("retrieval_latency_ms", sa.Float(), nullable=False),
        sa.Column("generation_latency_ms", sa.Float(), nullable=False),
        sa.Column("total_latency_ms", sa.Float(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("tokens_estimated", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["evaluation_run.id"],
            name=op.f("fk_evaluation_item_run_id_evaluation_run"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_item")),
    )
    op.create_index(
        op.f("ix_evaluation_item_run_id"),
        "evaluation_item",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_evaluation_item_run_id"),
        table_name="evaluation_item",
    )
    op.drop_table("evaluation_item")

    op.drop_index(
        op.f("ix_evaluation_run_created_by"),
        table_name="evaluation_run",
    )
    op.drop_index(
        op.f("ix_evaluation_run_workspace_id"),
        table_name="evaluation_run",
    )
    op.drop_table("evaluation_run")
