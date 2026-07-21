from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.database import get_db_session
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.repositories.document_parsing import DocumentParsingRepository
from app.tasks.document_parsing import parse_document_task
from app.utils.enum import DocumentParsingStatus


router = APIRouter()


@router.post(
    "/{document_id}/parse",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Documents Parsing"],
)
async def parse_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    repository = DocumentRepository(session)
    doc_parsing_repo = DocumentParsingRepository(session)

    document = await repository.get_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    # Phải kiểm tra user có quyền trong workspace.
    # Thay bằng permission service hiện tại của bạn.
    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this document.",
        )

    existing_document_parsing = (
        await doc_parsing_repo.get_by_document_id(document.id)
    )

    if existing_document_parsing is not None and existing_document_parsing.status in {
        DocumentParsingStatus.PARSING,
        DocumentParsingStatus.PARSING_QUEUED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document parsing is already in progress.",
        )

    document_parsing = (
        existing_document_parsing
        or await doc_parsing_repo.get_or_create_for_document(document)
    )

    await doc_parsing_repo.mark_parsing_queued(document_parsing)
    await session.commit()

    parse_document_task.delay(
        str(document.id)
    )

    return {
        "document_id": str(document.id),
        "status": DocumentParsingStatus.PARSING_QUEUED.value,
    }
