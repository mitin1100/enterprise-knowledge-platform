"""add document chunk and document chunking tables

Revision ID: a1f39d7c2b44
Revises: 6f2d9b1a8c3e
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "a1f39d7c2b44"
down_revision: Union[str, Sequence[str], None] = "6f2d9b1a8c3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "document_chunking",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "CHUNKING_QUEUED",
                "CHUNKING",
                "EMBEDDING",
                "COMPLETED",
                "FAILED",
                name="document_chunking_status",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("chunk_count", sa.Integer(), nullable=True),
        sa.Column(
            "embedding_model",
            sqlmodel.sql.sqltypes.AutoString(length=100),
            nullable=True,
        ),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=True),
        sa.Column("chunking_metadata", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["document.id"],
            name=op.f("fk_document_chunking_document_id_document"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("pk_document_chunking")
        ),
    )
    op.create_index(
        op.f("ix_document_chunking_document_id"),
        "document_chunking",
        ["document_id"],
        unique=True,
    )

    op.create_table(
        "document_chunk",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column(
            "embedding_id",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column("chunk_metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["document.id"],
            name=op.f("fk_document_chunk_document_id_document"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.id"],
            name=op.f("fk_document_chunk_workspace_id_workspace"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunk")),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunk_document_id_chunk_index",
        ),
    )
    op.create_index(
        op.f("ix_document_chunk_document_id"),
        "document_chunk",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_chunk_workspace_id"),
        "document_chunk",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_chunk_embedding_id"),
        "document_chunk",
        ["embedding_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_document_chunk_embedding_id"),
        table_name="document_chunk",
    )
    op.drop_index(
        op.f("ix_document_chunk_workspace_id"),
        table_name="document_chunk",
    )
    op.drop_index(
        op.f("ix_document_chunk_document_id"),
        table_name="document_chunk",
    )
    op.drop_table("document_chunk")

    op.drop_index(
        op.f("ix_document_chunking_document_id"),
        table_name="document_chunking",
    )
    op.drop_table("document_chunking")
