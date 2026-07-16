"""update schema users table name

Revision ID: e784fccf6207
Revises: 66b965cb79bd
Create Date: 2026-07-16 09:37:20.590159

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e784fccf6207"
down_revision: Union[str, Sequence[str], None] = "66b965cb79bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename user table to users while preserving existing data."""
    op.drop_constraint(
        "fk_workspace_owner_id_user",
        "workspace",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_conversation_user_id_user",
        "conversation",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_document_uploaded_by_user",
        "document",
        type_="foreignkey",
    )

    op.rename_table("user", "users")

    op.create_foreign_key(
        "fk_workspace_owner_id_users",
        "workspace",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_conversation_user_id_users",
        "conversation",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_document_uploaded_by_users",
        "document",
        "users",
        ["uploaded_by"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Rename users table back to user while preserving existing data."""
    op.drop_constraint(
        "fk_workspace_owner_id_users",
        "workspace",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_conversation_user_id_users",
        "conversation",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_document_uploaded_by_users",
        "document",
        type_="foreignkey",
    )

    op.rename_table("users", "user")

    op.create_foreign_key(
        "fk_workspace_owner_id_user",
        "workspace",
        "user",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_conversation_user_id_user",
        "conversation",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_document_uploaded_by_user",
        "document",
        "user",
        ["uploaded_by"],
        ["id"],
        ondelete="CASCADE",
    )
