from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.database import get_db_session
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import DocumentChunkRepository
from app.repositories.document_chunking import DocumentChunkingRepository
from app.repositories.document_parsing import DocumentParsingRepository
from app.schemas.chunking import (
    ChunkContextResponse,
    ChunkingTriggerResponse,
    ChunkListResponse,
    ChunkResponse,
)
from app.tasks.chunking import chunk_document_task
from app.utils.enum import ChunkingStatus, DocumentParsingStatus

router = APIRouter()


@router.post(
    "/{document_id}/chunk",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ChunkingTriggerResponse,
    tags=["Documents Chunking"],
)
async def chunk_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ChunkingTriggerResponse:
    repository = DocumentRepository(session)
    doc_parsing_repo = DocumentParsingRepository(session)
    chunking_repo = DocumentChunkingRepository(session)

    document = await repository.get_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this document.",
        )

    parsing = await doc_parsing_repo.get_by_document_id(document.id)

    if parsing is None or parsing.status != DocumentParsingStatus.PARSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document must be parsed before it can be chunked.",
        )

    existing_chunking = await chunking_repo.get_by_document_id(
        document.id
    )

    if existing_chunking is not None and existing_chunking.status in {
        ChunkingStatus.CHUNKING_QUEUED,
        ChunkingStatus.CHUNKING,
        ChunkingStatus.EMBEDDING,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document chunking is already in progress.",
        )

    chunking = (
        existing_chunking
        or await chunking_repo.get_or_create_for_document(document)
    )

    await chunking_repo.mark_queued(chunking)
    await session.commit()

    chunk_document_task.delay(str(document.id))

    return ChunkingTriggerResponse(
        document_id=document.id,
        status=ChunkingStatus.CHUNKING_QUEUED.value,
    )


@router.get(
    "/{document_id}/chunks",
    response_model=ChunkListResponse,
    tags=["Documents Chunking"],
)
async def list_document_chunks(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
) -> ChunkListResponse:
    repository = DocumentRepository(session)
    chunk_repository = DocumentChunkRepository(session)

    document = await repository.get_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this document.",
        )

    chunks = await chunk_repository.list_by_document(
        document_id=document_id,
        offset=offset,
        limit=limit,
    )

    total = await chunk_repository.count_by_document(document_id)

    return ChunkListResponse(
        items=[
            ChunkResponse.model_validate(chunk)
            for chunk in chunks
        ],
        total=total,
    )


@router.get(
    "/{document_id}/chunks/{chunk_index}/context",
    response_model=ChunkContextResponse,
    tags=["Documents Chunking"],
)
async def get_chunk_context(
    document_id: UUID,
    chunk_index: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ChunkContextResponse:
    """
    Fetch a single chunk plus its immediate neighbors, so a clicked
    citation can open the source document at that point and highlight
    the exact passage the answer relied on.
    """
    repository = DocumentRepository(session)
    chunk_repository = DocumentChunkRepository(session)

    document = await repository.get_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if document.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this document.",
        )

    chunk = await chunk_repository.get_by_document_and_index(
        document_id=document_id,
        chunk_index=chunk_index,
    )

    if chunk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found.",
        )

    previous_chunk, next_chunk = None, None

    if chunk_index > 0:
        previous_chunk = await chunk_repository.get_by_document_and_index(
            document_id=document_id,
            chunk_index=chunk_index - 1,
        )

    next_chunk = await chunk_repository.get_by_document_and_index(
        document_id=document_id,
        chunk_index=chunk_index + 1,
    )

    return ChunkContextResponse(
        document_id=document.id,
        document_name=document.original_filename,
        chunk=ChunkResponse.model_validate(chunk),
        previous=(
            ChunkResponse.model_validate(previous_chunk)
            if previous_chunk
            else None
        ),
        next=(
            ChunkResponse.model_validate(next_chunk)
            if next_chunk
            else None
        ),
    )
