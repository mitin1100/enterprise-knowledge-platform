from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        title: str | None,
    ) -> Conversation:
        conversation = Conversation(
            workspace_id=workspace_id,
            user_id=user_id,
            title=title,
        )

        self._session.add(conversation)
        await self._session.flush()
        await self._session.refresh(conversation)

        return conversation

    async def get_by_id_and_workspace(
        self,
        *,
        conversation_id: UUID,
        workspace_id: UUID,
    ) -> Conversation | None:
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.workspace_id == workspace_id,
        )

        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self,
        *,
        workspace_id: UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Conversation]:
        statement = (
            select(Conversation)
            .where(Conversation.workspace_id == workspace_id)
            .order_by(Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def count_by_workspace(self, workspace_id: UUID) -> int:
        statement = select(func.count(Conversation.id)).where(
            Conversation.workspace_id == workspace_id
        )

        result = await self._session.execute(statement)
        return result.scalar_one() or 0
