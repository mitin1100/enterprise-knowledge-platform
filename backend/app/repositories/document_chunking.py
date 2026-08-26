from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_chunking import DocumentChunking
from app.utils.enum import ChunkingStatus


class DocumentChunkingRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def get_by_document_id(
        self,
        document_id: UUID,
    ) -> DocumentChunking | None:
        statement = select(DocumentChunking).where(
            DocumentChunking.document_id == document_id
        )

        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_or_create_for_document(
        self,
        document: Document,
    ) -> DocumentChunking:
        chunking = await self.get_by_document_id(document.id)

        if chunking is not None:
            return chunking

        chunking = DocumentChunking(document_id=document.id)

        self._session.add(chunking)
        await self._session.flush()

        return chunking

    async def mark_queued(
        self,
        chunking: DocumentChunking,
    ) -> None:
        chunking.status = ChunkingStatus.CHUNKING_QUEUED
        chunking.error_message = None

        await self._session.flush()

    async def mark_chunking_started(
        self,
        chunking: DocumentChunking,
        chunking_metadata: dict,
    ) -> None:
        chunking.status = ChunkingStatus.CHUNKING
        chunking.chunking_metadata = chunking_metadata
        chunking.error_message = None

        await self._session.flush()

    async def mark_embedding_started(
        self,
        chunking: DocumentChunking,
        chunk_count: int,
    ) -> None:
        chunking.status = ChunkingStatus.EMBEDDING
        chunking.chunk_count = chunk_count

        await self._session.flush()

    async def mark_completed(
        self,
        chunking: DocumentChunking,
        chunk_count: int,
        embedding_model: str,
        embedding_dimensions: int,
    ) -> None:
        chunking.status = ChunkingStatus.COMPLETED
        chunking.chunk_count = chunk_count
        chunking.embedding_model = embedding_model
        chunking.embedding_dimensions = embedding_dimensions
        chunking.error_message = None

        await self._session.flush()

    async def mark_failed(
        self,
        chunking: DocumentChunking,
        error_message: str,
    ) -> None:
        chunking.status = ChunkingStatus.FAILED
        chunking.error_message = error_message

        await self._session.flush()
