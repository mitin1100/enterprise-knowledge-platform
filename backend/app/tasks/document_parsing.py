import asyncio
import logging
from uuid import UUID

from celery import Task

from app.core.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.parsing.exception import (
    DocumentNotFoundError,
    DocumentPageLimitExceededError,
    DocumentTooLargeError,
    EmptyDocumentError,
    UnsupportedDocumentTypeError,
)
from app.services.parsing.service import ParsingService
from app.services.storage.factory import get_storage_service

logger = logging.getLogger(__name__)


NON_RETRYABLE_PARSING_EXCEPTIONS = (
    DocumentNotFoundError,
    DocumentTooLargeError,
    DocumentPageLimitExceededError,
    UnsupportedDocumentTypeError,
    EmptyDocumentError,
)


@celery_app.task(
    bind=True,
    name="documents.parse",
    max_retries=3,
    soft_time_limit=20 * 60,
    time_limit=25 * 60,
    acks_late=True,
    reject_on_worker_lost=True,
)
def parse_document_task(
    self: Task,
    document_id: str,
) -> dict:
    try:
        return asyncio.run(
            _parse_document(document_id)
        )

    except NON_RETRYABLE_PARSING_EXCEPTIONS:
        logger.exception(
            "Document parsing failed with a non-retryable error",
            extra={"document_id": document_id},
        )
        raise

    except Exception as exc:
        logger.exception(
            "Document parsing failed with a retryable error",
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


async def _parse_document(
    document_id: str,
) -> dict:
    parsed_document_id = UUID(document_id)

    async with AsyncSessionLocal() as session:
        storage = await get_storage_service()

        service = ParsingService(
            session=session,
            storage=storage,
        )

        result = await service.parse_document(
            parsed_document_id
        )

        return {
            "document_id": document_id,
            "status": "parsed",
            "page_count": result.page_count,
            "character_count": result.character_count,
            "used_ocr": result.used_ocr,
            "ocr_page_count": result.ocr_page_count,
            "table_count": result.table_count,
        }


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
