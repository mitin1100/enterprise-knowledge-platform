import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document_chunk import DocumentChunk
from app.models.document_parsing import DocumentParsing
from app.repositories.document import DocumentRepository
from app.repositories.document_chunk import DocumentChunkRepository
from app.repositories.document_chunking import DocumentChunkingRepository
from app.repositories.document_parsing import DocumentParsingRepository
from app.schemas.chunking import ChunkingResult
from app.schemas.doc_parsing import ParsedPage
from app.services.chunking.exception import (
    DocumentNotFoundError,
    DocumentNotParsedError,
    EmptyChunkResultError,
)
from app.services.chunking.splitter import TextChunker
from app.services.chunking.tokenizer import Tokenizer
from app.services.embedding.base import EmbeddingService
from app.services.vectorstore.base import VectorRecord
from app.services.vectorstore.elasticsearch_store import (
    ElasticsearchVectorStore,
)
from app.utils.enum import DocumentParsingStatus

logger = logging.getLogger(__name__)


class ChunkingService:
    def __init__(
        self,
        session: AsyncSession,
        embedding_service: EmbeddingService,
        vector_store: ElasticsearchVectorStore,
    ) -> None:
        self._session = session
        self._embedding_service = embedding_service
        self._vector_store = vector_store

        self._document_repository = DocumentRepository(session)
        self._doc_parsing_repository = DocumentParsingRepository(session)
        self._chunking_repository = DocumentChunkingRepository(session)
        self._chunk_repository = DocumentChunkRepository(session)

        self._tokenizer = Tokenizer(settings.chunking_token_encoding)
        self._chunker = TextChunker(
            tokenizer=self._tokenizer,
            chunk_size_tokens=settings.chunk_size_tokens,
            chunk_overlap_tokens=settings.chunk_overlap_tokens,
            min_chunk_tokens=settings.chunk_min_tokens,
        )

    async def chunk_and_embed_document(
        self,
        document_id: UUID,
    ) -> ChunkingResult:
        document = await self._document_repository.get_by_id(
            document_id
        )

        if document is None:
            raise DocumentNotFoundError(
                f"Document {document_id} does not exist."
            )

        parsing = await self._doc_parsing_repository.get_by_document_id(
            document_id
        )

        if (
            parsing is None
            or parsing.status != DocumentParsingStatus.PARSED
            or not parsing.parsed_text
        ):
            raise DocumentNotParsedError(
                f"Document {document_id} has not been parsed "
                "successfully yet."
            )

        chunking = (
            await self._chunking_repository
            .get_or_create_for_document(document)
        )

        try:
            await self._chunking_repository.mark_chunking_started(
                chunking,
                chunking_metadata={
                    "chunk_size_tokens": settings.chunk_size_tokens,
                    "chunk_overlap_tokens": settings.chunk_overlap_tokens,
                    "min_chunk_tokens": settings.chunk_min_tokens,
                    "token_encoding": settings.chunking_token_encoding,
                },
            )
            await self._session.commit()

            pages = self._build_pages(parsing)
            drafts = self._chunker.chunk_pages(pages)

            if not drafts:
                raise EmptyChunkResultError(
                    f"Chunking produced no chunks for document "
                    f"{document_id}."
                )

            await self._chunking_repository.mark_embedding_started(
                chunking,
                chunk_count=len(drafts),
            )
            await self._session.commit()

            embeddings = await self._embedding_service.embed_texts(
                [draft.content for draft in drafts]
            )

            # Re-chunking replaces the previous set of chunks/vectors.
            await self._chunk_repository.delete_by_document(document_id)
            await self._vector_store.delete_by_document(str(document_id))

            db_chunks: list[DocumentChunk] = []
            vector_records: list[VectorRecord] = []

            for draft, embedding in zip(drafts, embeddings):
                embedding_id = f"{document_id}:{draft.chunk_index}"
                metadata = (
                    {"heading": draft.heading} if draft.heading else {}
                )

                db_chunks.append(
                    DocumentChunk(
                        document_id=document_id,
                        workspace_id=document.workspace_id,
                        chunk_index=draft.chunk_index,
                        content=draft.content,
                        page_number=draft.page_number,
                        token_count=draft.token_count,
                        embedding_id=embedding_id,
                        chunk_metadata=metadata or None,
                    )
                )

                vector_records.append(
                    VectorRecord(
                        id=embedding_id,
                        document_id=str(document_id),
                        workspace_id=str(document.workspace_id),
                        chunk_index=draft.chunk_index,
                        content=draft.content,
                        page_number=draft.page_number,
                        embedding=embedding,
                        metadata=metadata,
                    )
                )

            await self._chunk_repository.bulk_create(db_chunks)
            await self._vector_store.index_chunks(vector_records)

            await self._chunking_repository.mark_completed(
                chunking,
                chunk_count=len(db_chunks),
                embedding_model=self._embedding_service.model_name,
                embedding_dimensions=self._embedding_service.dimensions,
            )
            await self._session.commit()

            logger.info(
                "Document chunking completed",
                extra={
                    "document_id": str(document_id),
                    "chunk_count": len(db_chunks),
                },
            )

            return ChunkingResult(
                document_id=document_id,
                chunk_count=len(db_chunks),
                embedding_model=self._embedding_service.model_name,
                embedding_dimensions=self._embedding_service.dimensions,
            )

        except Exception as exc:
            await self._session.rollback()

            try:
                document = await self._document_repository.get_by_id(
                    document_id
                )

                if document is not None:
                    chunking = (
                        await self._chunking_repository
                        .get_or_create_for_document(document)
                    )

                    await self._chunking_repository.mark_failed(
                        chunking,
                        error_message=self._safe_error_message(exc),
                    )
                    await self._session.commit()

            except Exception:
                await self._session.rollback()

                logger.exception(
                    "Unable to persist chunking failure status",
                    extra={"document_id": str(document_id)},
                )

            raise

    @staticmethod
    def _build_pages(
        parsing: DocumentParsing,
    ) -> list[ParsedPage]:
        metadata = parsing.parse_metadata or {}
        page_texts = metadata.get("page_texts") or []

        pages = [
            ParsedPage(
                page_number=page["page_number"],
                text=page["text"],
            )
            for page in page_texts
            if page.get("text", "").strip()
        ]

        if pages:
            return pages

        return [ParsedPage(page_number=1, text=parsing.parsed_text)]

    @staticmethod
    def _safe_error_message(exception: Exception) -> str:
        message = str(exception).strip()

        if not message:
            message = exception.__class__.__name__

        return message[:2000]
