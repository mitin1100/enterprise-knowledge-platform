from dataclasses import dataclass, field


@dataclass(slots=True)
class VectorRecord:
    id: str
    document_id: str
    workspace_id: str
    chunk_index: int
    content: str
    page_number: int | None
    embedding: list[float]
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class SearchHit:
    id: str
    document_id: str
    workspace_id: str
    chunk_index: int
    content: str
    page_number: int | None
    score: float
    metadata: dict = field(default_factory=dict)
