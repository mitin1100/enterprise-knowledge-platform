
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Column, Enum as SQLEnum, ForeignKey, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlmodel import Field, Relationship
import sqlalchemy as sa

from app.models.base import BaseModel
from app.utils.enum import DocumentStatus, StorageProvider

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

    mime_type: str = Field(
        sa_column=Column(
            "mime_type",
            String,
            nullable=False,
        ),
        description="MIME type of the document (e.g., application/pdf, text/plain)",
    )

    doc_metadata: dict | None = Field(
        sa_column=Column(
            "doc_metadata",
            JSON,
            nullable=True,
        ),
        description="JSON metadata (chunk_size, overlap, external vectorID, etc.)",
    )

    @property
    def storage_key(self) -> str:
        return self.storage_path

    @property
    def file_extension(self) -> str:
        if self.doc_metadata and self.doc_metadata.get("file_extension"):
            return str(self.doc_metadata["file_extension"])

        return self.filename.rsplit(".", maxsplit=1)[-1]

    @property
    def storage_provider(self) -> StorageProvider:
        if self.doc_metadata and self.doc_metadata.get("storage_provider"):
            return StorageProvider(str(self.doc_metadata["storage_provider"]))

        return StorageProvider.LOCAL

    @property
    def checksum(self) -> str | None:
        if not self.doc_metadata:
            return None

        checksum = self.doc_metadata.get("checksum")
        return str(checksum) if checksum else None

