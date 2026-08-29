import asyncio
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.conversation import ConversationRepository
from app.repositories.document import DocumentRepository
from app.repositories.message import MessageRepository
from app.schemas.chat import ChatRequest, ChatResponse, Citation, MessageResponse
from app.schemas.retrieval import RetrievedChunk
from app.services.chat.exception import (
    ConversationNotFoundError,
    EmptyMessageError,
)
from app.services.generation.base import GenerationService
from app.services.retrieval.exception import EmptyQueryError
from app.services.retrieval.service import RetrievalService
from app.utils.enum import MessageRole

logger = logging.getLogger(__name__)


class ChatService:
    """
    Orchestrates the RAG answer flow: retrieve relevant chunks, build a
    grounded prompt, call the configured LLM, and persist both the user
    question and the generated answer (with citations) as messages.
    """

    def __init__(
        self,
        session: AsyncSession,
        retrieval_service: RetrievalService,
        generation_service: GenerationService,
    ) -> None:
        self._session = session
        self._retrieval_service = retrieval_service
        self._generation_service = generation_service

        self._conversation_repository = ConversationRepository(session)
        self._message_repository = MessageRepository(session)
        self._document_repository = DocumentRepository(session)

    async def ask(
        self,
        *,
        workspace_id: UUID,
        conversation_id: UUID,
        payload: ChatRequest,
    ) -> ChatResponse:
        conversation = (
            await self._conversation_repository.get_by_id_and_workspace(
                conversation_id=conversation_id,
                workspace_id=workspace_id,
            )
        )

        if conversation is None:
            raise ConversationNotFoundError(
                f"Conversation {conversation_id} does not exist."
            )

        question = payload.message.strip()

        if not question:
            raise EmptyMessageError("Message must not be empty.")

        user_message = await self._message_repository.create(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=question,
        )

        top_k = payload.top_k or settings.generation_context_chunk_limit

        try:
            retrieval = await self._retrieval_service.retrieve(
                query=question,
                workspace_id=str(workspace_id),
                level=payload.retrieval_level,
                top_k=top_k,
            )
        except EmptyQueryError as exc:
            raise EmptyMessageError(str(exc)) from exc

        context = retrieval.results[
            : settings.generation_context_chunk_limit
        ]

        generated = await self._generation_service.generate_answer(
            query=question,
            context=context,
        )

        citations = await self._build_citations(
            context,
            generated.cited_indices,
        )

        assistant_message = await self._message_repository.create(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=generated.answer,
            citations=[
                citation.model_dump(mode="json") for citation in citations
            ],
            message_metadata={
                "retrieval_level": payload.retrieval_level.value,
            },
        )

        await self._session.commit()

        return ChatResponse(
            conversation_id=conversation_id,
            user_message=MessageResponse.model_validate(user_message),
            assistant_message=MessageResponse.model_validate(
                assistant_message
            ),
        )

    async def _build_citations(
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

        document_ids = {
            UUID(chunk.document_id) for chunk in cited_chunks
        }

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
                score=chunk.score,
            )
            for chunk in cited_chunks
        ]
