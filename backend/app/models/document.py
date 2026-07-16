
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Column, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlmodel import Field, Relationship
import sqlalchemy as sa

from app.models.base import BaseModel
from app.utils.enum import DocumentStatus

if TYPE_CHECKING:
    from app.models.document_chunk import DocumentChunk
    from app.models.workspace import Workspace


class Document(BaseModel, table=True):
    __tablename__ = "document"

    id: UUID = Field(
        sa_column=Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            default=uuid4,
        ),
        description="Unique identifier for the document",
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
        description="ID of the workspace containing this document",
    )

    uploaded_by: UUID = Field(
        sa_column=Column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            index=True,
            nullable=False,
        ),
        description="ID of the user who uploaded the document",
    )

    filename: str = Field(
        sa_type=String,
        nullable=False,
        description="Stored filename",
    )

    original_filename: str = Field(
        sa_type=String,
        nullable=False,
        description="Original uploaded filename",
    )

    content_type: Optional[str] = Field(
        default=None,
        sa_type=String,
        description="MIME type of the uploaded document",
    )

    storage_path: str = Field(
        sa_type=Text,
        nullable=False,
        description="Path or object key where the document is stored",
    )

    file_size: Optional[int] = Field(
        default=None,
        sa_type=BigInteger,
        description="Document size in bytes",
    )

    status: DocumentStatus = Field(
        default=DocumentStatus.PENDING,
        sa_column=Column(
            SQLEnum(
                DocumentStatus,
                name="document_status",
                native_enum=False,
                values_callable=lambda enum_class: [
                    member.value for member in enum_class
                ],
            ),
            nullable=False,
            default=DocumentStatus.PENDING,
        ),
        description="Current processing status: UPLOADED, PROCESSING, INGESTED, FAILED",
    )

    error_message: Optional[str] = Field(
        default=None,
        sa_type=Text,
        description="Error details when document processing fails",
    )

    workspace: "Workspace" = Relationship(
        back_populates="documents",
    )

    chunks: list["DocumentChunk"] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
            "order_by": "DocumentChunk.chunk_index",
        },
    )

