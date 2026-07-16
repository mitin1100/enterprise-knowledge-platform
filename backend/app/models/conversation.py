from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, String
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.workspace import Workspace


class Conversation(BaseModel, table=True):
    __tablename__ = "conversation"

    id: UUID = Field(
            sa_column=Column(
                "id",
                sa.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                default=uuid4,
            ),
            description="Unique identifier for the conversation",
        )

    workspace_id: UUID = Field(
        sa_column=Column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey(
                "workspace.id",
                ondelete="CASCADE",
            ),
            index=True,
            nullable=False,
        ),
        description="ID of the workspace containing the conversation",
    )

    user_id: UUID = Field(
        sa_column=Column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            index=True,
            nullable=False,
        ),
        description="ID of the user who created the conversation",
    )

    title: Optional[str] = Field(
        default=None,
        sa_type=String(255),
        description="Optional conversation title",
    )

    workspace: "Workspace" = Relationship(
        back_populates="conversations",
    )

    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
            "order_by": "Message.created_at",
        },
    )
