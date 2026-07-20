from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.api.dependency import get_db, get_storage
from app.repositories.document import DocumentRepository
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.services.document import DocumentService
from app.services.storage.base import StorageService


router = APIRouter(
    prefix="/workspaces/{workspace_id}/documents",
    tags=["Documents"],
)


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    workspace_id: UUID,
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage),
) -> DocumentUploadResponse:
    service = DocumentService(
        db=db,
        storage=storage,
    )

    document = await service.upload_document(
        workspace_id=workspace_id,
        file=file,
        uploaded_by=current_user.id,
    )

    return DocumentUploadResponse(
        document=DocumentResponse.model_validate(document),
        message="Document uploaded and queued for processing",
    )


@router.get(
    "",
    response_model=DocumentListResponse,
)
async def list_documents(
    workspace_id: UUID,
    current_user: CurrentUser,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    repository = DocumentRepository(db)

    documents = await repository.list_by_workspace(
        workspace_id=workspace_id,
        offset=offset,
        limit=limit,
    )

    total = await repository.count_by_workspace(
        workspace_id=workspace_id,
    )

    return DocumentListResponse(
        items=[
            DocumentResponse.model_validate(document)
            for document in documents
        ],
        total=total,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    workspace_id: UUID,
    document_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    repository = DocumentRepository(db)

    document = await repository.get_by_id_and_workspace(
        document_id=document_id,
        workspace_id=workspace_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return DocumentResponse.model_validate(document)
