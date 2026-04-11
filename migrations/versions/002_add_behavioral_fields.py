"""add behavioral fields to trades — reason, rule_followed, mistake_category

Revision ID: 002_behavioral
Revises: 001_initial
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_behavioral"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("trades", sa.Column("reason", sa.String(200), nullable=True))
    op.add_column("trades", sa.Column("rule_followed", sa.Boolean(), nullable=True))
    op.add_column("trades", sa.Column("mistake_category", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("trades", "mistake_category")
    op.drop_column("trades", "rule_followed")
    op.drop_column("trades", "reason")
