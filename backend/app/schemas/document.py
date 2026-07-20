from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus
from app.utils.enum import StorageProvider


class DocumentResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    mime_type: str
    status: DocumentStatus
    storage_provider: StorageProvider
    error_message: str | None
    created_at: datetime
    uploaded_by: UUID

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str
    