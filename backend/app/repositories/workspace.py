from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        owner_id: UUID,
        name: str,
        description: str | None,
    ) -> Workspace:
        workspace = Workspace(
            owner_id=owner_id,
            name=name,
            description=description,
        )

        self.session.add(workspace)
        await self.session.flush()

        return workspace

    async def list_by_owner(
        self,
        owner_id: UUID,
    ) -> list[Workspace]:
        statement = (
            select(Workspace)
            .where(Workspace.owner_id == owner_id)
            .order_by(Workspace.created_at.desc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def get_by_id_and_owner(
        self,
        *,
        workspace_id: UUID,
        owner_id: UUID,
    ) -> Workspace | None:
        statement = select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.owner_id == owner_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def delete(self, workspace: Workspace) -> None:
        await self.session.delete(workspace)
        await self.session.flush()