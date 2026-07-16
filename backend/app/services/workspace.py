from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import WorkspaceNotFoundError
from app.models.workspace import Workspace
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreateRequest


class WorkspaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.workspace_repository = WorkspaceRepository(session)

    async def create_workspace(
        self,
        *,
        owner_id: UUID,
        request: WorkspaceCreateRequest,
    ) -> Workspace:
        workspace = await self.workspace_repository.create(
            owner_id=owner_id,
            name=request.name.strip(),
            description=(
                request.description.strip()
                if request.description
                else None
            ),
        )

        await self.session.commit()
        await self.session.refresh(workspace)

        return workspace

    async def list_workspaces(
        self,
        owner_id: UUID,
    ) -> list[Workspace]:
        return await self.workspace_repository.list_by_owner(
            owner_id,
        )

    async def get_workspace(
        self,
        *,
        workspace_id: UUID,
        owner_id: UUID,
    ) -> Workspace:
        workspace = (
            await self.workspace_repository.get_by_id_and_owner(
                workspace_id=workspace_id,
                owner_id=owner_id,
            )
        )

        if workspace is None:
            raise WorkspaceNotFoundError

        return workspace

    async def delete_workspace(
        self,
        *,
        workspace_id: UUID,
        owner_id: UUID,
    ) -> None:
        workspace = await self.get_workspace(
            workspace_id=workspace_id,
            owner_id=owner_id,
        )

        await self.workspace_repository.delete(workspace)
        await self.session.commit()