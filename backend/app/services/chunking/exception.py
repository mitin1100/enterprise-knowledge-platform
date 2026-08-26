class ChunkingError(Exception):
    """Base exception for document chunking."""


class DocumentNotFoundError(ChunkingError):
    """Raised when the requested document does not exist."""


class DocumentNotParsedError(ChunkingError):
    """Raised when chunking is requested before parsing has completed."""


class EmptyChunkResultError(ChunkingError):
    """Raised when chunking produced no usable chunks."""
