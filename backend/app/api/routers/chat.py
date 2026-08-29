from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.api.dependency import get_db, get_vector_store
from app.core.config import settings
from app.models.conversation import Conversation
from app.models.workspace import Workspace
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    MessageListResponse,
    MessageResponse,
)
from app.services.chat.exception import (
    ConversationNotFoundError,
    EmptyMessageError,
)
from app.services.chat.service import ChatService
from app.services.embedding.base import EmbeddingService
from app.services.embedding.factory import get_embedding_service
from app.services.generation.base import GenerationService
from app.services.generation.exception import GenerationError
from app.services.generation.factory import get_generation_service
from app.services.reranker.base import RerankerService
from app.services.reranker.factory import get_reranker_service
from app.services.retrieval.service import RetrievalService
from app.services.vectorstore.elasticsearch_store import (
    ElasticsearchVectorStore,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/conversations",
    tags=["Chat"],
)


async def _get_owned_workspace(
    workspace_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession,
) -> Workspace:
    workspace_repository = WorkspaceRepository(db)

    workspace = await workspace_repository.get_by_id_and_owner(
        workspace_id=workspace_id,
        owner_id=current_user.id,
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    return workspace


async def _get_owned_conversation(
    workspace_id: UUID,
    conversation_id: UUID,
    db: AsyncSession,
) -> Conversation:
    conversation_repository = ConversationRepository(db)

    conversation = await conversation_repository.get_by_id_and_workspace(
        conversation_id=conversation_id,
        workspace_id=workspace_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return conversation


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    workspace_id: UUID,
    payload: ConversationCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    await _get_owned_workspace(workspace_id, current_user, db)

    conversation_repository = ConversationRepository(db)

    conversation = await conversation_repository.create(
        workspace_id=workspace_id,
        user_id=current_user.id,
        title=payload.title,
    )

    await db.commit()

    return ConversationResponse.model_validate(conversation)


@router.get(
    "",
    response_model=ConversationListResponse,
)
async def list_conversations(
    workspace_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> ConversationListResponse:
    await _get_owned_workspace(workspace_id, current_user, db)

    conversation_repository = ConversationRepository(db)

    conversations = await conversation_repository.list_by_workspace(
        workspace_id=workspace_id,
        offset=offset,
        limit=limit,
    )
    total = await conversation_repository.count_by_workspace(workspace_id)

    return ConversationListResponse(
        items=[
            ConversationResponse.model_validate(conversation)
            for conversation in conversations
        ],
        total=total,
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def rename_conversation(
    workspace_id: UUID,
    conversation_id: UUID,
    payload: ConversationUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    await _get_owned_workspace(workspace_id, current_user, db)

    conversation = await _get_owned_conversation(
        workspace_id, conversation_id, db
    )

    conversation_repository = ConversationRepository(db)

    conversation = await conversation_repository.update_title(
        conversation=conversation,
        title=payload.title,
    )

    await db.commit()

    return ConversationResponse.model_validate(conversation)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    await _get_owned_workspace(workspace_id, current_user, db)

    conversation = await _get_owned_conversation(
        workspace_id, conversation_id, db
    )

    conversation_repository = ConversationRepository(db)

    await conversation_repository.delete(conversation)
    await db.commit()


@router.get(
    "/{conversation_id}/messages",
    response_model=MessageListResponse,
)
async def list_messages(
    workspace_id: UUID,
    conversation_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> MessageListResponse:
    await _get_owned_workspace(workspace_id, current_user, db)

    conversation_repository = ConversationRepository(db)

    conversation = await conversation_repository.get_by_id_and_workspace(
        conversation_id=conversation_id,
        workspace_id=workspace_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    message_repository = MessageRepository(db)

    messages = await message_repository.list_by_conversation(
        conversation_id=conversation_id,
        offset=offset,
        limit=limit,
    )
    total = await message_repository.count_by_conversation(
        conversation_id
    )

    return MessageListResponse(
        items=[
            MessageResponse.model_validate(message)
            for message in messages
        ],
        total=total,
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=ChatResponse,
)
async def send_message(
    workspace_id: UUID,
    conversation_id: UUID,
    payload: ChatRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    reranker_service: RerankerService = Depends(get_reranker_service),
    generation_service: GenerationService = Depends(get_generation_service),
    vector_store: ElasticsearchVectorStore = Depends(get_vector_store),
) -> ChatResponse:
    await _get_owned_workspace(workspace_id, current_user, db)

    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        reranker_service=reranker_service,
        candidate_k=settings.retrieval_candidate_k,
        rrf_k=settings.retrieval_rrf_k,
    )

    chat_service = ChatService(
        session=db,
        retrieval_service=retrieval_service,
        generation_service=generation_service,
    )

    try:
        return await chat_service.ask(
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            payload=payload,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except EmptyMessageError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
