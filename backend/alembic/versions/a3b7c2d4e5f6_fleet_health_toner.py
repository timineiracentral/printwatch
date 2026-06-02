"""fleet_health_toner

Revision ID: a3b7c2d4e5f6
Revises: 1e9f0b8a7e50
Create Date: 2026-06-02 14:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3b7c2d4e5f6"
down_revision: Union[str, None] = "1e9f0b8a7e50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "printers",
        sa.Column(
            "snmp_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "printers",
        sa.Column("snmp_community_override", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "printer_fleet_status",
        sa.Column("printer_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(), nullable=False),
        sa.Column("error_message", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(
            ["printer_id"],
            ["printers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("printer_id"),
    )

    op.create_table(
        "printer_toner_snapshots",
        sa.Column("printer_id", sa.Integer(), nullable=False),
        sa.Column("black_pct", sa.Integer(), nullable=True),
        sa.Column("color_pct", sa.Integer(), nullable=True),
        sa.Column(
            "partial_color",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["printer_id"],
            ["printers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("printer_id"),
    )
    op.create_index(
        "ix_printer_toner_snapshots_checked_at",
        "printer_toner_snapshots",
        ["checked_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_printer_toner_snapshots_checked_at",
        table_name="printer_toner_snapshots",
    )
    op.drop_table("printer_toner_snapshots")
    op.drop_table("printer_fleet_status")
    op.drop_column("printers", "snmp_community_override")
    op.drop_column("printers", "snmp_enabled")
