from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.api.dependency import get_db, get_vector_store
from app.core.config import settings
from app.repositories.workspace import WorkspaceRepository
from app.schemas.retrieval import (
    RetrievalLevel,
    RetrievalRequest,
    RetrievalResponse,
)
from app.services.embedding.base import EmbeddingService
from app.services.embedding.factory import get_embedding_service
from app.services.reranker.base import RerankerService
from app.services.reranker.factory import get_reranker_service
from app.services.retrieval.exception import EmptyQueryError
from app.services.retrieval.service import RetrievalService
from app.services.vectorstore.elasticsearch_store import (
    ElasticsearchVectorStore,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/retrieval",
    tags=["Retrieval"],
)


@router.post(
    "/search",
    response_model=RetrievalResponse,
)
async def search_chunks(
    workspace_id: UUID,
    payload: RetrievalRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    reranker_service: RerankerService = Depends(get_reranker_service),
    vector_store: ElasticsearchVectorStore = Depends(get_vector_store),
) -> RetrievalResponse:
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

    service = RetrievalService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        reranker_service=reranker_service,
        candidate_k=settings.retrieval_candidate_k,
        rrf_k=settings.retrieval_rrf_k,
    )

    default_top_k = (
        settings.retrieval_rerank_top_k
        if payload.level == RetrievalLevel.HYBRID_RERANKED
        else settings.retrieval_top_k
    )

    try:
        return await service.retrieve(
            query=payload.query,
            workspace_id=str(workspace_id),
            level=payload.level,
            top_k=payload.top_k or default_top_k,
        )
    except EmptyQueryError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
