"""fix document parsing status length

Revision ID: 9c4f6a2e5d1b
Revises: feb8a8c64c37
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c4f6a2e5d1b"
down_revision: Union[str, Sequence[str], None] = "feb8a8c64c37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE table_name = 'document_parsing'
                  AND constraint_name = 'document_parsing_status'
                  AND constraint_type = 'CHECK'
            ) THEN
                ALTER TABLE document_parsing
                DROP CONSTRAINT document_parsing_status;
            END IF;
        END $$;
        """
    )

    op.alter_column(
        "document_parsing",
        "status",
        existing_type=sa.String(length=7),
        type_=sa.String(length=32),
        existing_nullable=False,
    )

    op.execute(
        """
        UPDATE document_parsing
        SET status = 'PARSING_QUEUED'
        WHERE status = 'PENDING';
        """
    )

    op.create_check_constraint(
        "ck_document_parsing_status",
        "document_parsing",
        "status IN ('PARSING_QUEUED', 'PARSING', 'PARSED', 'FAILED')",
    )

    op.drop_index(
        op.f("ix_document_parsing_document_id"),
        table_name="document_parsing",
    )
    op.create_index(
        op.f("ix_document_parsing_document_id"),
        "document_parsing",
        ["document_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_document_parsing_document_id"),
        table_name="document_parsing",
    )
    op.create_index(
        op.f("ix_document_parsing_document_id"),
        "document_parsing",
        ["document_id"],
        unique=False,
    )

    op.drop_constraint(
        "ck_document_parsing_status",
        "document_parsing",
        type_="check",
    )

    op.alter_column(
        "document_parsing",
        "status",
        existing_type=sa.String(length=32),
        type_=sa.String(length=7),
        existing_nullable=False,
    )
