from enum import StrEnum

class DocumentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    UPLOADED = "UPLOADED"
    FAILED = "FAILED"

class DocumentParsingStatus(StrEnum):
    PARSING_QUEUED = "PARSING_QUEUED"
    PARSING = "PARSING"
    PARSED = "PARSED"
    FAILED = "FAILED"
    
class DocumentIngestionStatus(StrEnum):
    """Document ingestion processing status."""

    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    DEDICATED = "DEDICATED"
    INGESTED = "INGESTED"
    FAILED = "FAILED"

class MessageRole(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class StorageProvider(StrEnum):
    LOCAL = "LOCAL"
    MINIO = "MINIO"
