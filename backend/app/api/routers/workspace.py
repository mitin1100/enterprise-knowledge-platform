from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import CurrentUser
from app.api.dependencies.database import get_db_session
from app.core.exceptions import WorkspaceNotFoundError
from app.schemas.workspace import (
    WorkspaceCreateRequest,
    WorkspaceResponse,
)
from app.services.workspace import WorkspaceService


router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"],
)


@router.post("",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace(
    request: WorkspaceCreateRequest,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> WorkspaceResponse:
    service = WorkspaceService(session)

    workspace = await service.create_workspace(
        owner_id=current_user.id,
        request=request,
    )

    return WorkspaceResponse.model_validate(workspace)


@router.get("",
    response_model=list[WorkspaceResponse],
)
async def list_workspaces(
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> list[WorkspaceResponse]:
    service = WorkspaceService(session)

    workspaces = await service.list_workspaces(
        current_user.id,
    )

    return [
        WorkspaceResponse.model_validate(workspace)
        for workspace in workspaces
    ]


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
)
async def get_workspace(
    workspace_id: UUID,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> WorkspaceResponse:
    service = WorkspaceService(session)

    try:
        workspace = await service.get_workspace(
            workspace_id=workspace_id,
            owner_id=current_user.id,
        )
    except WorkspaceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return WorkspaceResponse.model_validate(workspace)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workspace(
    workspace_id: UUID,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> Response:
    service = WorkspaceService(session)

    try:
        await service.delete_workspace(
            workspace_id=workspace_id,
            owner_id=current_user.id,
        )
    except WorkspaceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)