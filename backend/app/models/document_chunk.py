from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
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
            name="uq_document_chunks_document_id_chunk_index",
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
        description="Unique identifier for the doc chunk",
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

    chunk_index: int = Field(
        sa_type=Integer,
        nullable=False,
        description="Position of the chunk within the document",
    )

    content: str = Field(
        sa_type=Text,
        nullable=False,
        description="Text content of the document chunk",
    )

    token_count: Optional[int] = Field(
        default=None,
        sa_type=Integer,
        description="Number of tokens in the chunk",
    )

    page_number: Optional[int] = Field(
        default=None,
        sa_type=Integer,
        description="Source page number of the chunk",
    )

    chunk_metadata: dict = Field(
        default_factory=dict,
        sa_column=Column(
            JSONB,
            nullable=False,
            default=dict,
        ),
        description="Additional metadata associated with the chunk",
    )

    document: "Document" = Relationship(
        back_populates="chunks",
    )
