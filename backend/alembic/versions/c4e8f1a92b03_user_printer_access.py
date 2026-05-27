"""user_printer_access

Revision ID: c4e8f1a92b03
Revises: 085a2d5c5767
Create Date: 2026-05-27 20:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4e8f1a92b03"
down_revision: Union[str, None] = "085a2d5c5767"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_printer_access",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("printer_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["printer_id"], ["printers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "printer_id", name="uq_user_printer"),
    )
    op.create_index(
        "ix_user_printer_access_user_id",
        "user_printer_access",
        ["user_id"],
    )
    op.create_index(
        "ix_user_printer_access_printer_id",
        "user_printer_access",
        ["printer_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_printer_access_printer_id", table_name="user_printer_access")
    op.drop_index("ix_user_printer_access_user_id", table_name="user_printer_access")
    op.drop_table("user_printer_access")
