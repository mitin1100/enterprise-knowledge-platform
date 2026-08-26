class RetrievalError(Exception):
    """Base exception for retrieval."""


class EmptyQueryError(RetrievalError):
    """Raised when the search query is empty after normalization."""
