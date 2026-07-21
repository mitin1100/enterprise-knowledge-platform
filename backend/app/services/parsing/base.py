from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.doc_parsing import ParseResult


class BaseDocumentParser(ABC):
    supported_extensions: frozenset[str] = frozenset()
    supported_mime_types: frozenset[str] = frozenset()

    def supports(
        self,
        file_path: Path,
        mime_type: str | None,
    ) -> bool:
        normalized_extension = file_path.suffix.lower()
        normalized_mime_type = (mime_type or "").lower().strip()

        return (
            normalized_extension in self.supported_extensions
            or normalized_mime_type in self.supported_mime_types
        )

    @abstractmethod
    def parse(
        self,
        file_path: Path,
        mime_type: str | None = None,
    ) -> ParseResult:
        """
        Parse a local document file.

        This method is synchronous because third-party document libraries
        perform blocking CPU/file-system work. ParsingService invokes it
        through asyncio.to_thread().
        """
        raise NotImplementedError
    