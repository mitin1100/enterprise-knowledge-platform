from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.utils.enum import DocumentStatus
from app.utils.enum import StorageProvider


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        document_id: UUID,
        workspace_id: UUID,
        original_filename: str,
        stored_filename: str,
        storage_key: str,
        storage_provider: StorageProvider,
        mime_type: str,
        file_extension: str,
        file_size: int,
        checksum: str,
        uploaded_by: UUID,
    ) -> Document:
        document = Document(
            id=document_id,
            workspace_id=workspace_id,
            uploaded_by=uploaded_by,
            filename=stored_filename,
            original_filename=original_filename,
            doc_uri=storage_key,
            mime_type=mime_type,
            file_size=file_size,
            status=DocumentStatus.PENDING,
            doc_metadata={
                "checksum": checksum,
                "file_extension": file_extension,
                "storage_provider": storage_provider.value,
            },
        )

        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        return document

    async def get_by_id(
        self,
        document_id: UUID,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id
        )

        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id_and_workspace(
        self,
        document_id: UUID,
        workspace_id: UUID,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
        )

        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self,
        workspace_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Document]:
        statement = (
            select(Document)
            .where(Document.workspace_id == workspace_id)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def count_by_workspace(
        self,
        workspace_id: UUID,
    ) -> int:
        statement = (
            select(func.count(Document.id))
            .where(Document.workspace_id == workspace_id)
        )

        result = await self.db.execute(statement)
        return result.scalar_one() or 0

    async def find_duplicate(
        self,
        workspace_id: UUID,
        checksum: str,
    ) -> Document | None:
        statement = select(Document).where(
            Document.workspace_id == workspace_id,
            Document.doc_metadata["checksum"].as_string() == checksum,
            Document.status != DocumentStatus.FAILED,
        )

        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        document: Document,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> Document:
        document.status = status
        document.error_message = error_message

        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        return document
