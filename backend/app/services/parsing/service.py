import asyncio
import logging
import tempfile
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.document import DocumentRepository
from app.repositories.document_parsing import DocumentParsingRepository
from app.schemas.doc_parsing import ParseResult
from app.services.parsing.cleaner import TextCleaner
from app.services.parsing.exception import (
    DocumentNotFoundError,
    DocumentTooLargeError,
    ParsingError,
)
from app.services.parsing.parsers.docx_parser import (
    DocxDocumentParser,
)
from app.services.parsing.parsers.pdf_parser import (
    PdfDocumentParser,
)
from app.services.parsing.parsers.text_parser import (
    TextDocumentParser,
)
from app.services.parsing.registry import ParserRegistry
from app.services.storage.base import StorageService

logger = logging.getLogger(__name__)


class ParsingService:
    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
    ) -> None:
        self._session = session
        self._storage = storage
        self._document_repository = DocumentRepository(session)
        self._doc_parsing_repository = DocumentParsingRepository(session)

        cleaner = TextCleaner(
            header_footer_ratio=(
                settings.parsing_header_footer_ratio
            ),
            max_output_chars=(
                settings.parsing_max_output_chars
            ),
        )

        self._registry = ParserRegistry(
            parsers=[
                PdfDocumentParser(
                    cleaner=cleaner,
                    max_pages=settings.parsing_max_pdf_pages,
                    ocr_enabled=settings.parsing_ocr_enabled,
                    ocr_languages=(
                        settings.parsing_ocr_languages
                    ),
                    ocr_dpi=settings.parsing_ocr_dpi,
                    minimum_page_text_length=(
                        settings.parsing_min_page_text_length
                    ),
                ),
                DocxDocumentParser(cleaner=cleaner),
                TextDocumentParser(cleaner=cleaner),
            ]
        )

    async def parse_document(
        self,
        document_id: UUID,
    ) -> ParseResult:
        document = await self._document_repository.get_by_id(
            document_id
        )

        if document is None:
            raise DocumentNotFoundError(
                f"Document {document_id} does not exist."
            )

        self._validate_document_size(
            size_bytes=document.file_size
        )

        document_parsing = (
            await self._doc_parsing_repository
            .get_or_create_for_document(document)
        )

        await self._doc_parsing_repository.mark_parsing_started(
            document_parsing=document_parsing,
        )
        await self._session.commit()

        try:
            with tempfile.TemporaryDirectory(
                prefix=f"document-{document_id}-"
            ) as temporary_directory:
                temporary_path = Path(temporary_directory)

                safe_filename = self._safe_filename(
                    document.filename
                )

                local_file_path = (
                    temporary_path / safe_filename
                )

                await self._download_original_file(
                    storage_key=document.storage_key,
                    destination=local_file_path,
                )

                parser = self._registry.get_parser(
                    file_path=local_file_path,
                    mime_type=document.mime_type,
                )

                result = await asyncio.to_thread(
                    parser.parse,
                    local_file_path,
                    document.mime_type,
                )

            await self._doc_parsing_repository.mark_parsing_completed(
                document_parsing=document_parsing,
                parsed_text=result.text,
                page_count=result.page_count,
                character_count=result.character_count,
                metadata={
                    "detected_type": result.detected_type,
                    "detected_encoding": (
                        result.detected_encoding
                    ),
                    "used_ocr": result.used_ocr,
                    "ocr_page_count": result.ocr_page_count,
                    "table_count": result.table_count,
                    "warnings": result.warnings,
                    **result.metadata,
                },
            )

            await self._session.commit()

            logger.info(
                "Document parsing completed",
                extra={
                    "document_id": str(document_id),
                    "character_count": result.character_count,
                    "page_count": result.page_count,
                    "used_ocr": result.used_ocr,
                },
            )

            return result

        except Exception as exc:
            await self._session.rollback()

            try:
                document = (
                    await self._document_repository.get_by_id(
                        document_id
                    )
                )

                if document is not None:
                    document_parsing = (
                        await self._doc_parsing_repository
                        .get_or_create_for_document(document)
                    )

                    await (
                        self._doc_parsing_repository
                        .mark_parsing_failed(
                            document_parsing=document_parsing,
                            error_message=self._safe_error_message(
                                exc
                            ),
                        )
                    )

                    await self._session.commit()

            except Exception:
                await self._session.rollback()

                logger.exception(
                    "Unable to persist parsing failure status",
                    extra={
                        "document_id": str(document_id),
                    },
                )

            raise

    def _validate_document_size(
        self,
        size_bytes: int | None,
    ) -> None:
        if size_bytes is None:
            return

        maximum_bytes = (
            settings.parsing_max_file_size_mb
            * 1024
            * 1024
        )

        if size_bytes > maximum_bytes:
            raise DocumentTooLargeError(
                f"Document size is {size_bytes} bytes, exceeding "
                f"the configured limit of {maximum_bytes} bytes."
            )

    async def _download_original_file(
        self,
        storage_key: str,
        destination: Path,
    ) -> None:
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Adapt this call to the actual method in your BaseStorage.
        await self._storage.download_file(
            storage_key=storage_key,
            destination=destination,
        )

        if not destination.exists():
            raise ParsingError(
                "Storage download completed without creating "
                "the destination file."
            )

    @staticmethod
    def _safe_filename(filename: str | None) -> str:
        if not filename:
            return "document.bin"

        # Path(...).name prevents path traversal such as ../../file.pdf
        safe_name = Path(filename).name

        return safe_name or "document.bin"

    @staticmethod
    def _safe_error_message(
        exception: Exception,
    ) -> str:
        message = str(exception).strip()

        if not message:
            message = exception.__class__.__name__

        # Avoid storing huge exception contents in the database.
        return message[:2000]
    
