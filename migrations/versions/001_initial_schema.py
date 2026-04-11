"""initial schema — baseline of all existing tables

Revision ID: 001_initial
Revises: None
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(320), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(128), nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("plan", sa.String(20), server_default="free"),
        sa.Column("role", sa.String(20), server_default="user"),
        sa.Column("timezone_offset", sa.Integer(), server_default="0"),
        sa.Column("failed_login_count", sa.Integer(), server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "plan IN ('free', 'pro', 'prop_trader', 'enterprise')",
            name="ck_user_plan",
        ),
    )

    op.create_table(
        "trades",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("symbol", sa.String(50), nullable=False, index=True),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("pnl", sa.Float(), nullable=False),
        sa.Column("duration_minutes", sa.Float(), nullable=True),
        sa.Column("setup_type", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("fees", sa.Float(), server_default="0"),
        sa.Column("source", sa.String(20), nullable=True),
        sa.Column("mood", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("side IN ('BUY', 'SELL')", name="ck_trade_side"),
    )
    op.create_index("ix_trades_user_timestamp", "trades", ["user_id", "timestamp"])
    op.create_index("ix_trades_timestamp", "trades", ["timestamp"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "broker_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("broker", sa.String(50), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token_value", sa.Text(), nullable=True),
        sa.Column("api_key", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "prop_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("firm", sa.String(50), nullable=False),
        sa.Column("phase", sa.String(30), nullable=False),
        sa.Column("initial_balance", sa.Float(), nullable=False),
        sa.Column("daily_loss_limit_pct", sa.Float(), server_default="5.0"),
        sa.Column("max_drawdown_pct", sa.Float(), server_default="10.0"),
        sa.Column("drawdown_type", sa.String(20), server_default="'static'"),
        sa.Column("profit_target_pct", sa.Float(), nullable=True),
        sa.Column("min_trading_days", sa.Integer(), server_default="10"),
        sa.Column("consistency_rule_pct", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column("status", sa.String(20), server_default="'active'"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("prop_accounts")
    op.drop_table("broker_connections")
    op.drop_table("audit_logs")
    op.drop_table("trades")
    op.drop_table("users")
