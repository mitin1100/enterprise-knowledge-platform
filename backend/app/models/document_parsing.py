from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Column, Enum as SQLEnum, ForeignKey, String, Text, JSON
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlmodel import Field, Relationship
from app.utils.enum import DocumentParsingStatus

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.document import Document


class DocumentParsing(BaseModel, table=True):
    __tablename__ = "document_parsing"

    id: UUID = Field(
        sa_column=Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            default=uuid4,
        ),
        description="Unique identifier for the doc parsing",
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

    status: DocumentParsingStatus = Field(
            default=DocumentParsingStatus.PARSING_QUEUED,
            sa_column=Column(
                SQLEnum(
                    DocumentParsingStatus,
                    name="document_parsing_status",
                    native_enum=False,
                    values_callable=lambda enum_class: [
                        member.value for member in enum_class
                    ],
                    length=32,
                ),
                nullable=False,
                default=DocumentParsingStatus.PARSING_QUEUED,
            ),
            description="Current processing status: PARSING_QUEUED, PARSING, PARSED, FAILED",
        )

    parsed_text: str | None = Field(
        default=None,
        sa_type=Text,
    )

    character_count: int | None = Field(
        default=None,
        sa_type=BigInteger,
    )

    page_count: int | None = Field(
        default=None,
    )

    parser_name: str | None = Field(
        default=None,
        max_length=100,
    )

    parser_version: str | None = Field(
        default=None,
        max_length=50,
    )

    parse_metadata: dict | None = Field(
        default=None,
        sa_column=Column(
            JSON,
            nullable=True,
        ),
    )

    error_message: str | None = Field(
        default=None,
        sa_type=Text,
    )


    document: "Document" = Relationship(
        back_populates="parsings",
    )
