"""add last_export_at to users

Revision ID: 004_export
Revises: 003_rules
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_export"
down_revision: Union[str, None] = "003_rules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_export_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_export_at")
