import asyncio
from datetime import datetime, timezone
from uuid import UUID

from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.repositories.document import DocumentRepository
from app.services.storage.factory import get_storage_service
from app.utils.enum import DocumentStatus


logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_document(
    self,
    document_id: str,
) -> dict:
    return asyncio.run(process_document_async(document_id))


async def process_document_async(
    document_id: str,
) -> dict:
    storage = await get_storage_service()

    async with AsyncSessionLocal() as db:
        repository = DocumentRepository(db)

        try:
            document = await repository.get_by_id(UUID(document_id))

            if document is None:
                logger.error(
                    "Document %s was not found",
                    document_id,
                )
                return {
                    "document_id": document_id,
                    "status": "not_found",
                }

            if document.status == DocumentStatus.UPLOADED:
                return {
                    "document_id": document_id,
                    "status": "already_completed",
                }

            metadata = dict(document.doc_metadata or {})
            metadata["processing_started_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            document.status = DocumentStatus.PROCESSING
            document.doc_metadata = metadata
            document.error_message = None

            db.add(document)
            await db.commit()

            if not await storage.exists(document.storage_key):
                raise FileNotFoundError(
                    f"Storage object not found: {document.storage_key}"
                )

            file_content = await storage.download(document.storage_key)

            validate_document_readability(
                extension=document.file_extension,
                content=file_content,
            )

            # Next phases:
            # 1. Extract text
            # 2. Normalize text
            # 3. Chunk document
            # 4. Generate embedding
            # 5. Save chunks/vector

            metadata = dict(document.doc_metadata or {})
            metadata["processing_completed_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            document.status = DocumentStatus.UPLOADED
            document.doc_metadata = metadata
            document.error_message = None

            db.add(document)
            await db.commit()

            return {
                "document_id": document_id,
                "status": DocumentStatus.UPLOADED.value,
            }

        except Exception as exc:
            await db.rollback()

            document = await repository.get_by_id(UUID(document_id))

            if document is not None:
                metadata = dict(document.doc_metadata or {})
                metadata["processing_completed_at"] = datetime.now(
                    timezone.utc
            ).isoformat()

                document.status = DocumentStatus.FAILED
                document.doc_metadata = metadata
                document.error_message = str(exc)[:2000]

                db.add(document)
                await db.commit()

            logger.exception(
                "Document processing failed: %s",
                document_id,
            )

            raise


def validate_document_readability(
    extension: str,
    content: bytes,
) -> None:
    if not content:
        raise ValueError("Stored document is empty")

    if extension == "pdf":
        if not content.startswith(b"%PDF"):
            raise ValueError("Stored PDF is invalid")

    elif extension == "docx":
        if not content.startswith(b"PK"):
            raise ValueError("Stored DOCX is invalid")

    elif extension in {"txt", "md", "csv"}:
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise ValueError(
                    f"{extension.upper()} file is not valid UTF-8"
                ) from exc

    else:
        raise ValueError(
            f"Unsupported extension: {extension}"
        )
