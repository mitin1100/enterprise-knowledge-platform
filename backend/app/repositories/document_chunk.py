from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk


class DocumentChunkRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def bulk_create(
        self,
        chunks: list[DocumentChunk],
    ) -> list[DocumentChunk]:
        self._session.add_all(chunks)
        await self._session.flush()

        return chunks

    async def delete_by_document(
        self,
        document_id: UUID,
    ) -> None:
        statement = delete(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        )

        await self._session.execute(statement)
        await self._session.flush()

    async def get_by_document_and_index(
        self,
        document_id: UUID,
        chunk_index: int,
    ) -> DocumentChunk | None:
        statement = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.chunk_index == chunk_index,
        )

        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_document(
        self,
        document_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .offset(offset)
            .limit(limit)
        )

        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def count_by_document(
        self,
        document_id: UUID,
    ) -> int:
        statement = select(func.count(DocumentChunk.id)).where(
            DocumentChunk.document_id == document_id
        )

        result = await self._session.execute(statement)
        return result.scalar_one() or 0
