from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.api.dependency import get_db, get_vector_store
from app.core.config import settings
from app.repositories.evaluation import EvaluationRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.evaluation import (
    EvaluationDatasetParseResponse,
    EvaluationRunListResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationRunSummary,
)
from app.services.embedding.base import EmbeddingService
from app.services.embedding.factory import get_embedding_service
from app.services.evaluation.dataset import parse_dataset_file
from app.services.evaluation.exception import EmptyDatasetError, InvalidDatasetError
from app.services.evaluation.service import EvaluationService
from app.services.generation.base import GenerationService
from app.services.generation.exception import GenerationError
from app.services.generation.factory import get_generation_service
from app.services.reranker.base import RerankerService
from app.services.reranker.factory import get_reranker_service
from app.services.retrieval.service import RetrievalService
from app.services.vectorstore.elasticsearch_store import ElasticsearchVectorStore

router = APIRouter(
    prefix="/workspaces/{workspace_id}/evaluations",
    tags=["Evaluation"],
)


async def _assert_owned_workspace(
    workspace_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession,
) -> None:
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


@router.post(
    "/datasets/parse",
    response_model=EvaluationDatasetParseResponse,
)
async def parse_dataset(
    workspace_id: UUID,
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> EvaluationDatasetParseResponse:
    """
    Parse an uploaded JSON/CSV evaluation dataset file into rows the
    caller can preview and edit before submitting an evaluation run.
    """
    await _assert_owned_workspace(workspace_id, current_user, db)

    content = await file.read()

    try:
        items = parse_dataset_file(file.filename or "dataset.json", content)
    except InvalidDatasetError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return EvaluationDatasetParseResponse(items=items)


@router.post(
    "/runs",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_evaluation_run(
    workspace_id: UUID,
    payload: EvaluationRunRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    reranker_service: RerankerService = Depends(get_reranker_service),
    generation_service: GenerationService = Depends(get_generation_service),
    vector_store: ElasticsearchVectorStore = Depends(get_vector_store),
) -> EvaluationRunResponse:
    await _assert_owned_workspace(workspace_id, current_user, db)

    if len(payload.items) > settings.evaluation_max_dataset_items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Dataset has too many items: "
                f"{len(payload.items)} > {settings.evaluation_max_dataset_items}."
            ),
        )

    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        reranker_service=reranker_service,
        candidate_k=settings.retrieval_candidate_k,
        rrf_k=settings.retrieval_rrf_k,
    )

    evaluation_service = EvaluationService(
        session=db,
        retrieval_service=retrieval_service,
        generation_service=generation_service,
        embedding_service=embedding_service,
    )

    try:
        return await evaluation_service.run_evaluation(
            workspace_id=workspace_id,
            user_id=current_user.id,
            payload=payload,
        )
    except EmptyDatasetError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get(
    "/runs",
    response_model=EvaluationRunListResponse,
)
async def list_evaluation_runs(
    workspace_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> EvaluationRunListResponse:
    await _assert_owned_workspace(workspace_id, current_user, db)

    evaluation_repository = EvaluationRepository(db)

    runs = await evaluation_repository.list_by_workspace(
        workspace_id=workspace_id,
        offset=offset,
        limit=limit,
    )
    total = await evaluation_repository.count_by_workspace(workspace_id)

    return EvaluationRunListResponse(
        items=[EvaluationRunSummary.model_validate(run) for run in runs],
        total=total,
    )


@router.get(
    "/runs/{run_id}",
    response_model=EvaluationRunResponse,
)
async def get_evaluation_run(
    workspace_id: UUID,
    run_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> EvaluationRunResponse:
    await _assert_owned_workspace(workspace_id, current_user, db)

    evaluation_repository = EvaluationRepository(db)

    run = await evaluation_repository.get_by_id_and_workspace(
        run_id=run_id,
        workspace_id=workspace_id,
    )

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation run not found.",
        )

    return EvaluationService.to_run_response(run)
