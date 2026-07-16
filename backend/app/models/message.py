from app.utils.enum import MessageRole
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Column, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.conversation import Conversation



class Message(BaseModel, table=True):
    __tablename__ = "message"

    id: UUID = Field(
            sa_column=Column(
                "id",
                sa.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                default=uuid4,
            ),
            description="Unique identifier for the message",
        )
    
    conversation_id: UUID = Field(
        sa_column=Column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey(
                "conversation.id",
                ondelete="CASCADE",
            ),
            index=True,
            nullable=False,
        ),
        description="ID of the parent conversation",
    )

    role: MessageRole = Field(
        sa_column=Column(
            SQLEnum(
                MessageRole,
                name="message_role",
                native_enum=False,
                values_callable=lambda enum_class: [
                    member.value for member in enum_class
                ],
            ),
            nullable=False,
        ),
        description="Role of the message sender",
    )

    content: str = Field(
        sa_type=Text,
        nullable=False,
        description="Message text content",
    )

    citations: list = Field(
        default_factory=list,
        sa_column=Column(
            JSONB,
            nullable=False,
            default=list,
        ),
        description="List of citations associated with the message",
    )

    message_metadata: dict = Field(
        default_factory=dict,
        sa_column=Column(
            JSONB,
            nullable=False,
            default=dict,
        ),
        description="Additional metadata associated with the message",
    )

    conversation: "Conversation" = Relationship(
        back_populates="messages",
    )
