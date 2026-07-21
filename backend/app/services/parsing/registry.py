from pathlib import Path

from app.services.parsing.base import BaseDocumentParser
from app.services.parsing.exception import (
    UnsupportedDocumentTypeError,
)


class ParserRegistry:
    def __init__(
        self,
        parsers: list[BaseDocumentParser],
    ) -> None:
        self._parsers = parsers

    def get_parser(
        self,
        file_path: Path,
        mime_type: str | None,
    ) -> BaseDocumentParser:
        for parser in self._parsers:
            if parser.supports(
                file_path=file_path,
                mime_type=mime_type,
            ):
                return parser

        raise UnsupportedDocumentTypeError(
            "Unsupported document type. "
            f"Extension={file_path.suffix!r}, "
            f"MIME type={mime_type!r}."
        )
    