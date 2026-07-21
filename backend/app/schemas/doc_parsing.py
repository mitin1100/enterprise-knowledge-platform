from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ParsedPage(BaseModel):
    page_number: int = Field(ge=1)
    text: str

    used_ocr: bool = False
    table_count: int = Field(default=0, ge=0)

    metadata: dict[str, Any] = Field(default_factory=dict)


class ParseResult(BaseModel):
    text: str

    page_count: int = Field(default=0, ge=0)
    character_count: int = Field(default=0, ge=0)

    detected_type: str
    detected_encoding: str | None = None

    used_ocr: bool = False
    ocr_page_count: int = Field(default=0, ge=0)
    table_count: int = Field(default=0, ge=0)

    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DocumentParsingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    mime_type: str | None
    size_bytes: int | None

    parsing_status: str
    parsing_error: str | None

    parsed_character_count: int | None
    parsed_page_count: int | None
    parsing_metadata: dict[str, Any] | None

    