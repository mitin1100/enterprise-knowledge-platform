from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_parsing import DocumentParsing
from app.utils.enum import DocumentParsingStatus


class DocumentParsingRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def get_by_id(
        self,
        parsing_id: UUID,
    ) -> DocumentParsing | None:
        statement = select(DocumentParsing).where(
            DocumentParsing.id == parsing_id
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_document_id(
        self,
        document_id: UUID,
    ) -> DocumentParsing | None:
        statement = select(DocumentParsing).where(
            DocumentParsing.document_id == document_id
        )

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def get_or_create_for_document(
        self,
        document: Document,
    ) -> DocumentParsing:
        document_parsing = await self.get_by_document_id(
            document.id
        )

        if document_parsing is not None:
            return document_parsing

        document_parsing = DocumentParsing(
            document_id=document.id,
        )

        self._session.add(document_parsing)
        await self._session.flush()

        return document_parsing

    async def mark_parsing_queued(
        self,
        document_parsing: DocumentParsing,
    ) -> None:
        document_parsing.status = (
            DocumentParsingStatus.PARSING_QUEUED
        )
        document_parsing.error_message = None

        await self._session.flush()

    async def mark_parsing_started(
        self,
        document_parsing: DocumentParsing,
        # started_at: datetime,
    ) -> None:
        document_parsing.status = (
            DocumentParsingStatus.PARSING
        )
        # document_parsing.parsing_started_at = started_at
        # document_parsing.parsing_completed_at = None
        document_parsing.error_message = None

        await self._session.flush()

    async def mark_parsing_completed(
        self,
        document_parsing: DocumentParsing,
        parsed_text: str,
        page_count: int,
        character_count: int,
        metadata: dict,
        # completed_at: datetime,
    ) -> None:
        document_parsing.parsed_text = parsed_text
        document_parsing.page_count = page_count
        document_parsing.character_count = character_count
        document_parsing.parse_metadata = metadata

        document_parsing.status = (
            DocumentParsingStatus.PARSED
        )
        document_parsing.error_message = None
        # document_parsing.parsing_completed_at = completed_at

        await self._session.flush()

    async def mark_parsing_failed(
        self,
        document_parsing: DocumentParsing,
        error_message: str,
        # completed_at: datetime,
    ) -> None:
        document_parsing.status = (
            DocumentParsingStatus.FAILED
        )
        document_parsing.error_message = error_message
        # document_parsing.parsing_completed_at = completed_at

        await self._session.flush()
