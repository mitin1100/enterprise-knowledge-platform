class ParsingError(Exception):
    """Base exception for document parsing."""


class DocumentNotFoundError(ParsingError):
    """Raised when the requested document does not exist."""


class UnsupportedDocumentTypeError(ParsingError):
    """Raised when no parser supports the document type."""


class DocumentTooLargeError(ParsingError):
    """Raised when the document exceeds the configured size limit."""


class DocumentPageLimitExceededError(ParsingError):
    """Raised when a PDF exceeds the configured page limit."""


class EmptyDocumentError(ParsingError):
    """Raised when no meaningful text could be extracted."""


class OCRUnavailableError(ParsingError):
    """Raised when OCR is required but not available."""


class ParserExecutionError(ParsingError):
    """Raised when the selected parser cannot process the file."""