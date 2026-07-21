import logging
from pathlib import Path
from typing import Any

import pymupdf

from app.schemas.doc_parsing import ParseResult
from app.services.parsing.base import BaseDocumentParser
from app.services.parsing.cleaner import PageContent, TextCleaner
from app.services.parsing.exception import (
    DocumentPageLimitExceededError,
    EmptyDocumentError,
    OCRUnavailableError,
    ParserExecutionError,
)

logger = logging.getLogger(__name__)


class PdfDocumentParser(BaseDocumentParser):
    supported_extensions = frozenset({".pdf"})
    supported_mime_types = frozenset({"application/pdf"})

    def __init__(
        self,
        cleaner: TextCleaner,
        *,
        max_pages: int,
        ocr_enabled: bool,
        ocr_languages: str,
        ocr_dpi: int,
        minimum_page_text_length: int,
    ) -> None:
        self._cleaner = cleaner
        self._max_pages = max_pages
        self._ocr_enabled = ocr_enabled
        self._ocr_languages = ocr_languages
        self._ocr_dpi = ocr_dpi
        self._minimum_page_text_length = (
            minimum_page_text_length
        )

    def parse(
        self,
        file_path: Path,
        mime_type: str | None = None,
    ) -> ParseResult:
        try:
            document = pymupdf.open(str(file_path))
        except Exception as exc:
            raise ParserExecutionError(
                f"Unable to open PDF document: {exc}"
            ) from exc

        try:
            if document.is_encrypted:
                authenticated = document.authenticate("")

                if not authenticated:
                    raise ParserExecutionError(
                        "Password-protected PDFs are not supported."
                    )

            page_count = document.page_count

            if page_count > self._max_pages:
                raise DocumentPageLimitExceededError(
                    f"PDF has {page_count} pages, exceeding the "
                    f"configured limit of {self._max_pages} pages."
                )

            pages: list[PageContent] = []
            warnings: list[str] = []

            ocr_page_count = 0
            table_count = 0

            page_metadata: list[dict[str, Any]] = []

            for page_index in range(page_count):
                page = document.load_page(page_index)

                page_text = self._extract_native_text(page)

                tables_text, current_table_count = (
                    self._extract_tables(page)
                )

                table_count += current_table_count

                used_ocr = False

                if self._should_run_ocr(page, page_text):
                    if self._ocr_enabled:
                        try:
                            ocr_text = self._extract_ocr_text(page)

                            if len(ocr_text.strip()) > len(
                                page_text.strip()
                            ):
                                page_text = ocr_text
                                used_ocr = True
                                ocr_page_count += 1

                        except OCRUnavailableError:
                            raise

                        except Exception as exc:
                            logger.exception(
                                "OCR failed for PDF page %s",
                                page_index + 1,
                            )

                            warnings.append(
                                f"OCR failed on page "
                                f"{page_index + 1}: {exc}"
                            )
                    else:
                        warnings.append(
                            f"Page {page_index + 1} appears to be "
                            "image-based, but OCR is disabled."
                        )

                combined_page_text = self._combine_page_content(
                    page_text=page_text,
                    tables_text=tables_text,
                )

                pages.append(
                    PageContent(
                        page_number=page_index + 1,
                        text=combined_page_text,
                    )
                )

                page_metadata.append(
                    {
                        "page_number": page_index + 1,
                        "used_ocr": used_ocr,
                        "table_count": current_table_count,
                        "native_character_count": len(
                            page_text.strip()
                        ),
                        "image_count": len(
                            page.get_images(full=True)
                        ),
                    }
                )

            cleaned_text, cleaner_warnings = (
                self._cleaner.clean_pages(pages)
            )

            warnings.extend(cleaner_warnings)

            if not cleaned_text.strip():
                raise EmptyDocumentError(
                    "The PDF contains no extractable text."
                )

            return ParseResult(
                text=cleaned_text,
                page_count=page_count,
                character_count=len(cleaned_text),
                detected_type="pdf",
                detected_encoding=None,
                used_ocr=ocr_page_count > 0,
                ocr_page_count=ocr_page_count,
                table_count=table_count,
                warnings=warnings,
                metadata={
                    "pdf_metadata": self._sanitize_metadata(
                        document.metadata or {}
                    ),
                    "pages": page_metadata,
                },
            )

        finally:
            document.close()

    @staticmethod
    def _extract_native_text(
        page: pymupdf.Page,
    ) -> str:
        """
        sort=True attempts to restore a more natural reading order
        based on page coordinates.
        """
        return page.get_text(
            "text",
            sort=True,
        ).strip()

    def _should_run_ocr(
        self,
        page: pymupdf.Page,
        native_text: str,
    ) -> bool:
        text_length = len(native_text.strip())

        if text_length >= self._minimum_page_text_length:
            return False

        images = page.get_images(full=True)

        # No text and at least one image is a strong indication that the
        # page may be scanned.
        return bool(images) or text_length == 0

    def _extract_ocr_text(
        self,
        page: pymupdf.Page,
    ) -> str:
        try:
            text_page = page.get_textpage_ocr(
                language=self._ocr_languages,
                dpi=self._ocr_dpi,
                full=True,
            )
        except RuntimeError as exc:
            message = str(exc).lower()

            if (
                "tesseract" in message
                or "tessdata" in message
                or "ocr initialisation" in message
            ):
                raise OCRUnavailableError(
                    "Tesseract OCR is unavailable or its language "
                    "data is not installed correctly."
                ) from exc

            raise

        return page.get_text(
            "text",
            textpage=text_page,
            sort=True,
        ).strip()

    def _extract_tables(
        self,
        page: pymupdf.Page,
    ) -> tuple[str, int]:
        """
        Convert detected PDF tables to Markdown.

        Table extraction failure must not fail the entire page because
        ordinary text extraction may still be useful.
        """
        try:
            table_finder = page.find_tables()
        except Exception:
            logger.exception(
                "Table detection failed on page %s",
                page.number + 1,
            )
            return "", 0

        markdown_tables: list[str] = []

        for table_index, table in enumerate(
            table_finder.tables,
            start=1,
        ):
            try:
                extracted_rows = table.extract()
            except Exception:
                logger.exception(
                    "Table extraction failed for page %s table %s",
                    page.number + 1,
                    table_index,
                )
                continue

            markdown = self._rows_to_markdown(extracted_rows)

            if markdown:
                markdown_tables.append(
                    f"[Table {table_index}]\n{markdown}"
                )

        return (
            "\n\n".join(markdown_tables),
            len(markdown_tables),
        )

    @staticmethod
    def _rows_to_markdown(
        rows: list[list[str | None]],
    ) -> str:
        normalized_rows: list[list[str]] = []

        for row in rows:
            normalized_row = [
                (value or "")
                .replace("\n", " ")
                .replace("|", "\\|")
                .strip()
                for value in row
            ]

            if any(normalized_row):
                normalized_rows.append(normalized_row)

        if not normalized_rows:
            return ""

        maximum_columns = max(
            len(row)
            for row in normalized_rows
        )

        normalized_rows = [
            row + [""] * (maximum_columns - len(row))
            for row in normalized_rows
        ]

        header = normalized_rows[0]
        separator = ["---"] * maximum_columns

        output = [
            f"| {' | '.join(header)} |",
            f"| {' | '.join(separator)} |",
        ]

        output.extend(
            f"| {' | '.join(row)} |"
            for row in normalized_rows[1:]
        )

        return "\n".join(output)

    @staticmethod
    def _combine_page_content(
        page_text: str,
        tables_text: str,
    ) -> str:
        sections = []

        if page_text.strip():
            sections.append(page_text.strip())

        if tables_text.strip():
            sections.append(tables_text.strip())

        return "\n\n".join(sections)

    @staticmethod
    def _sanitize_metadata(
        metadata: dict[str, Any],
    ) -> dict[str, str | None]:
        return {
            str(key): (
                str(value)
                if value is not None
                else None
            )
            for key, value in metadata.items()
        }
    