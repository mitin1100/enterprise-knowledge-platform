import asyncio
import uuid
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import Document
from app.models.workspace import Workspace
from app.repositories.document import DocumentRepository
from app.services.storage.base import StorageService
from app.tasks.document import process_document
from app.utils.enum import DocumentStatus, StorageProvider
from app.utils.file_hash import calculate_sha256
from app.utils.file_validation import validate_upload_file


class DocumentService:
    def __init__(
        self,
        db: AsyncSession,
        storage: StorageService,
    ):
        self.db = db
        self.storage = storage
        self.repository = DocumentRepository(db)
        self.settings = get_settings()

    async def upload_document(
        self,
        *,
        workspace_id: UUID,
        file: UploadFile,
        uploaded_by: UUID,
    ) -> Document:
        workspace = await self.db.get(Workspace, workspace_id)

        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        validated_file = await validate_upload_file(
            file=file,
        )

        max_size_bytes = (
            self.settings.max_upload_size_mb
            * 1024
            * 1024
        )

        if validated_file.size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    "File size exceeds the maximum allowed size of "
                    f"{self.settings.max_upload_size_mb} MB"
                ),
            )

        checksum = await asyncio.to_thread(
            calculate_sha256,
            file.file,
        )

        duplicate = await self.repository.find_duplicate(
            workspace_id=workspace_id,
            checksum=checksum,
        )

        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "This document already exists in workspace",
                    "document_id": str(duplicate.id),
                },
            )

        document_id = uuid.uuid4()
        stored_filename = f"original.{validated_file.extension}"

        storage_key = (
            f"workspaces/{workspace_id}/"
            f"documents/{document_id}/"
            f"{stored_filename}"
        )

        storage_uploaded = False

        try:
            await self.storage.upload(
                file_object=file.file,
                storage_key=storage_key,
                content_type=validated_file.mime_type,
            )
            storage_uploaded = True

            document = await self.repository.create(
                document_id=document_id,
                workspace_id=workspace_id,
                original_filename=validated_file.original_filename,
                stored_filename=stored_filename,
                storage_key=storage_key,
                storage_provider=StorageProvider(
                    self.settings.STORAGE_PROVIDER.upper()
                ),
                mime_type=validated_file.mime_type,
                file_extension=validated_file.extension,
                file_size=validated_file.size,
                checksum=checksum,
                uploaded_by=uploaded_by,
            )

            await self.db.commit()
            await self.db.refresh(document)

        except Exception:
            await self.db.rollback()

            if storage_uploaded:
                await self.storage.delete(storage_key)

            raise

        try:
            process_document.delay(str(document.id))
        except Exception as exc:
            document.status = DocumentStatus.FAILED
            document.error_message = (
                f"Failed to enqueue processing task: {exc}"
            )

            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document was stored but processing could not be queued",
            ) from exc

        return document
