"""replace completed document status with uploaded

Revision ID: 6f2d9b1a8c3e
Revises: 9c4f6a2e5d1b
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f2d9b1a8c3e"
down_revision: Union[str, Sequence[str], None] = "9c4f6a2e5d1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    _drop_document_status_constraint()

    op.alter_column(
        "document",
        "status",
        existing_type=sa.String(length=10),
        type_=sa.String(length=10),
        existing_nullable=False,
    )

    op.execute(
        """
        UPDATE document
        SET status = 'UPLOADED'
        WHERE status = 'COMPLETED';
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    _drop_document_status_constraint()

    op.execute(
        """
        UPDATE document
        SET status = 'COMPLETED'
        WHERE status = 'UPLOADED';
        """
    )

    op.alter_column(
        "document",
        "status",
        existing_type=sa.String(length=10),
        type_=sa.String(length=10),
        existing_nullable=False,
    )


def _drop_document_status_constraint() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE table_name = 'document'
                  AND constraint_name = 'document_status'
                  AND constraint_type = 'CHECK'
            ) THEN
                ALTER TABLE document DROP CONSTRAINT document_status;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE table_name = 'document'
                  AND constraint_name = 'ck_document_status'
                  AND constraint_type = 'CHECK'
            ) THEN
                ALTER TABLE document DROP CONSTRAINT ck_document_status;
            END IF;
        END $$;
        """
    )
