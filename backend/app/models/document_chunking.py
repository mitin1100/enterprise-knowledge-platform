from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Enum as SQLEnum, ForeignKey, Integer, JSON, String, Text
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlmodel import Field, Relationship

from app.models.base import BaseModel
from app.utils.enum import ChunkingStatus

if TYPE_CHECKING:
    from app.models.document import Document


class DocumentChunking(BaseModel, table=True):
    __tablename__ = "document_chunking"

    id: UUID = Field(
        sa_column=Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            default=uuid4,
        ),
        description="Unique identifier for the chunking run",
    )

    document_id: UUID = Field(
        sa_column=Column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey(
                "document.id",
                ondelete="CASCADE",
            ),
            index=True,
            unique=True,
            nullable=False,
        ),
        description="ID of the parent document",
    )

    status: ChunkingStatus = Field(
        default=ChunkingStatus.CHUNKING_QUEUED,
        sa_column=Column(
            SQLEnum(
                ChunkingStatus,
                name="document_chunking_status",
                native_enum=False,
                values_callable=lambda enum_class: [
                    member.value for member in enum_class
                ],
                length=32,
            ),
            nullable=False,
            default=ChunkingStatus.CHUNKING_QUEUED,
        ),
        description=(
            "Current pipeline status: CHUNKING_QUEUED, CHUNKING, "
            "EMBEDDING, COMPLETED, FAILED"
        ),
    )

    chunk_count: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
    )

    embedding_model: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100), nullable=True),
    )

    embedding_dimensions: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
    )

    chunking_metadata: Optional[dict] = Field(
        default=None,
        sa_column=Column(
            JSON,
            nullable=True,
        ),
        description="Chunking configuration used, e.g. chunk size/overlap",
    )

    error_message: Optional[str] = Field(
        default=None,
        sa_type=Text,
    )

    document: "Document" = Relationship(
        back_populates="chunking",
    )
