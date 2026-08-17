"""paid confirmation — SoT columns on invoices

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-17 14:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "invoices",
        sa.Column(
            "admin_settled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "invoices",
        sa.Column(
            "user_paid_pending_recheck",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "invoices",
        sa.Column("user_paid_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "invoices",
        sa.Column("user_paid_contact_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "invoices",
        sa.Column("recheck_after", sa.Date(), nullable=True),
    )
    op.add_column(
        "invoices",
        sa.Column(
            "confirm_cycle",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("invoices", "confirm_cycle")
    op.drop_column("invoices", "recheck_after")
    op.drop_column("invoices", "user_paid_contact_id")
    op.drop_column("invoices", "user_paid_at")
    op.drop_column("invoices", "user_paid_pending_recheck")
    op.drop_column("invoices", "admin_settled")
