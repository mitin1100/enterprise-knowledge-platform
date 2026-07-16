from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlalchemy import Boolean, Integer, String, text
from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.workspace import Workspace


class User(BaseModel, table=True):

    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False,
        description="Unique identifier for the user",
    )

    email: str = Field(
        sa_type=String,
        unique=True,
        nullable=False,
        description="User email for authentication",
    )

    hashed_password: str = Field(
        sa_type=String,
        nullable=False,
        description="Hashed password",
    )

    full_name: str = Field(
        sa_type=String,
        nullable=False,
        description="User's full name",
    )

    is_active: bool = Field(
        default=True,
        nullable=False,
        description="User's status"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),

    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        description="Last update timestamp",
    )

    # Định nghĩa quan hệ (Relationship) trong SQLModel
    workspaces: list["Workspace"] = Relationship(
        back_populates="owner"
    )

