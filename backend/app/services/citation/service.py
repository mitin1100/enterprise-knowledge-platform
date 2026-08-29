import asyncio
from uuid import UUID

from app.repositories.document import DocumentRepository
from app.schemas.chat import Citation
from app.schemas.retrieval import RetrievedChunk

PREVIEW_MAX_CHARS = 240


class CitationService:
    """
    Turns the retrieved chunks a generation actually relied on into
    displayable `Citation` records: document name, page number, a short
    text preview, and the relevance score, ready for the frontend to
    render as "Sources" and to look up the full source chunk on click.
    """

    def __init__(self, document_repository: DocumentRepository) -> None:
        self._document_repository = document_repository

    async def build_citations(
        self,
        context: list[RetrievedChunk],
        cited_indices: list[int],
    ) -> list[Citation]:
        cited_chunks = [
            context[index]
            for index in cited_indices
            if 0 <= index < len(context)
        ]

        if not cited_chunks:
            return []

        document_ids = {UUID(chunk.document_id) for chunk in cited_chunks}

        documents = await asyncio.gather(
            *(
                self._document_repository.get_by_id(document_id)
                for document_id in document_ids
            )
        )

        names_by_id = {
            str(document.id): document.original_filename
            for document in documents
            if document is not None
        }

        return [
            Citation(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                document_name=names_by_id.get(chunk.document_id),
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                chunk_preview=make_preview(chunk.content),
                score=chunk.score,
            )
            for chunk in cited_chunks
        ]


def make_preview(
    content: str,
    *,
    max_chars: int = PREVIEW_MAX_CHARS,
) -> str:
    text = " ".join(content.split())

    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars].rsplit(" ", 1)[0]

    return f"{truncated}…"
