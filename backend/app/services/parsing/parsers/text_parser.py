from pathlib import Path

from charset_normalizer import from_bytes

from app.schemas.doc_parsing import ParseResult
from app.services.parsing.base import BaseDocumentParser
from app.services.parsing.cleaner import PageContent, TextCleaner
from app.services.parsing.exception import EmptyDocumentError


class TextDocumentParser(BaseDocumentParser):
    supported_extensions = frozenset(
        {
            ".txt",
            ".md",
            ".csv",
            ".log",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
        }
    )

    supported_mime_types = frozenset(
        {
            "text/plain",
            "text/markdown",
            "text/csv",
            "application/json",
            "application/xml",
            "text/xml",
            "application/yaml",
            "text/yaml",
        }
    )

    def __init__(self, cleaner: TextCleaner) -> None:
        self._cleaner = cleaner

    def parse(
        self,
        file_path: Path,
        mime_type: str | None = None,
    ) -> ParseResult:
        raw_bytes = file_path.read_bytes()

        detected = from_bytes(raw_bytes).best()

        if detected is None:
            # Last-resort fallback. Replacement characters are preferable
            # to failing the entire pipeline.
            text = raw_bytes.decode(
                "utf-8",
                errors="replace",
            )
            encoding = "utf-8-fallback"
            warnings = [
                "Encoding could not be detected reliably. "
                "UTF-8 fallback with replacement characters was used."
            ]
        else:
            text = str(detected)
            encoding = detected.encoding
            warnings = []

        cleaned_text, cleaner_warnings = self._cleaner.clean_pages(
            [
                PageContent(
                    page_number=1,
                    text=text,
                )
            ]
        )

        warnings.extend(cleaner_warnings)

        if not cleaned_text.strip():
            raise EmptyDocumentError(
                "The text document contains no extractable text."
            )

        return ParseResult(
            text=cleaned_text,
            page_count=1,
            character_count=len(cleaned_text),
            detected_type="text",
            detected_encoding=encoding,
            used_ocr=False,
            ocr_page_count=0,
            table_count=0,
            warnings=warnings,
            metadata={
                "source_extension": file_path.suffix.lower(),
            },
        )
    