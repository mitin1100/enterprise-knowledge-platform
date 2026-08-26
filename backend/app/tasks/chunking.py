import asyncio
import logging
from uuid import UUID

from celery import Task

from app.core.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.chunking.exception import (
    DocumentNotFoundError,
    DocumentNotParsedError,
    EmptyChunkResultError,
)
from app.services.chunking.service import ChunkingService
from app.services.embedding.factory import get_embedding_service
from app.services.vectorstore.factory import get_vector_store

logger = logging.getLogger(__name__)


NON_RETRYABLE_CHUNKING_EXCEPTIONS = (
    DocumentNotFoundError,
    DocumentNotParsedError,
    EmptyChunkResultError,
)


@celery_app.task(
    bind=True,
    name="documents.chunk",
    max_retries=3,
    soft_time_limit=20 * 60,
    time_limit=25 * 60,
    acks_late=True,
    reject_on_worker_lost=True,
)
def chunk_document_task(
    self: Task,
    document_id: str,
) -> dict:
    try:
        return asyncio.run(
            _chunk_document(document_id)
        )

    except NON_RETRYABLE_CHUNKING_EXCEPTIONS:
        logger.exception(
            "Document chunking failed with a non-retryable error",
            extra={"document_id": document_id},
        )
        raise

    except Exception as exc:
        logger.exception(
            "Document chunking failed with a retryable error",
            extra={
                "document_id": document_id,
                "retry_count": self.request.retries,
            },
        )

        raise self.retry(
            exc=exc,
            countdown=_retry_delay(
                retry_count=self.request.retries,
            ),
        )


async def _chunk_document(
    document_id: str,
) -> dict:
    parsed_document_id = UUID(document_id)

    embedding_service = get_embedding_service()
    vector_store = get_vector_store()

    try:
        async with AsyncSessionLocal() as session:
            service = ChunkingService(
                session=session,
                embedding_service=embedding_service,
                vector_store=vector_store,
            )

            result = await service.chunk_and_embed_document(
                parsed_document_id
            )

            return {
                "document_id": document_id,
                "status": "completed",
                "chunk_count": result.chunk_count,
                "embedding_model": result.embedding_model,
                "embedding_dimensions": result.embedding_dimensions,
            }

    finally:
        await vector_store.close()


def _retry_delay(
    retry_count: int,
) -> int:
    """
    Exponential backoff:
    retry 0 -> 30 seconds
    retry 1 -> 60 seconds
    retry 2 -> 120 seconds
    """
    return min(
        30 * (2**retry_count),
        5 * 60,
    )
