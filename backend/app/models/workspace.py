from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4
import datetime
from sqlalchemy import Column, ForeignKey, String, Text, func
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.user import User

class Workspace(BaseModel, table=True):
    __tablename__ = "workspace"

    id: UUID = Field(
            sa_column=Column(
                "id",
                sa.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                default=uuid4,
            ),
            description="Unique identifier for the workspace",
        )
    
    name: str = Field(
        sa_type=String,
        nullable=False,
        description="Workspace name",
    )

    description: Optional[str] = Field(
        default=None,
        sa_type=Text,
        description="Optional workspace description",
    )

    owner_id: UUID = Field(
        sa_column=Column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            index=True,
            nullable=False,
        ),
        description="ID of the user who owns this workspace",
    )

    owner: "User" = Relationship(
        back_populates="workspaces",
    )

    documents: list["Document"] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )

    conversations: list["Conversation"] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )

#     updated_at: datetime = Field(
#     sa_column_kwargs={
#         "server_default": func.now(),
#         "onupdate": func.now(),
#     },
#     nullable=False,
#     description="Record update timestamp (UTC)",
# )
