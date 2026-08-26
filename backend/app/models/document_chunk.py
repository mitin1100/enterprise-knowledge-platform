from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.document import Document


class DocumentChunk(BaseModel, table=True):
    __tablename__ = "document_chunk"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunk_document_id_chunk_index",
        ),
    )

    id: UUID = Field(
        sa_column=Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            default=uuid4,
        ),
        description="Unique identifier for the chunk",
    )

    document_id: UUID = Field(
        sa_column=Column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey(
                "document.id",
                ondelete="CASCADE",
            ),
            index=True,
            nullable=False,
        ),
        description="ID of the parent document",
    )

    workspace_id: UUID = Field(
        sa_column=Column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey(
                "workspace.id",
                ondelete="CASCADE",
            ),
            index=True,
            nullable=False,
        ),
        description="ID of the workspace, denormalized for scoped search",
    )

    chunk_index: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Position of the chunk within the document, starting at 0",
    )

    content: str = Field(
        sa_type=Text,
        nullable=False,
        description="Chunk text content",
    )

    page_number: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="Source page number for citation, when available",
    )

    token_count: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Number of tokens in the chunk content",
    )

    embedding_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String(255), nullable=True, index=True),
        description="ID of the corresponding vector document in the vector store",
    )

    chunk_metadata: Optional[dict] = Field(
        default=None,
        sa_column=Column(
            JSON,
            nullable=True,
        ),
        description="Extra metadata such as heading, char offsets, embedding model",
    )

    document: "Document" = Relationship(
        back_populates="chunks",
    )
