"""cost_rates

Revision ID: 4227505c4a72
Revises: c4e8f1a92b03
Create Date: 2026-05-27 16:55:05.546770

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "4227505c4a72"
down_revision: Union[str, None] = "c4e8f1a92b03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cost_rates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("rate_mono", sa.Numeric(12, 4), nullable=False),
        sa.Column("rate_color", sa.Numeric(12, 4), nullable=False),
        sa.Column("valid_from", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cost_rates_valid_from",
        "cost_rates",
        ["valid_from"],
    )

    with op.batch_alter_table("print_jobs") as batch_op:
        batch_op.add_column(
            sa.Column("color_mode_source", sa.String(length=20), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("print_jobs") as batch_op:
        batch_op.drop_column("color_mode_source")

    op.drop_index("ix_cost_rates_valid_from", table_name="cost_rates")
    op.drop_table("cost_rates")
