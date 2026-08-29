from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.utils.enum import MessageRole


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        citations: list[dict] | None = None,
        message_metadata: dict | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations or [],
            message_metadata=message_metadata or {},
        )

        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)

        return message

    async def list_by_conversation(
        self,
        conversation_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Message]:
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(offset)
            .limit(limit)
        )

        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def count_by_conversation(
        self,
        conversation_id: UUID,
    ) -> int:
        statement = select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id
        )

        result = await self._session.execute(statement)
        return result.scalar_one() or 0
