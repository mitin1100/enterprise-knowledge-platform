from datetime import datetime

from sqlalchemy import MetaData, func
from sqlmodel import Field, SQLModel

master_metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    },
)


class Base(SQLModel):
    metadata = master_metadata


class BaseModel(Base):
    """Base model for entity tables"""

    __abstract__ = True

    created_at: datetime = Field(
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
        description="Record creation timestamp (UTC)",
    )
