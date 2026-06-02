"""printer_meter_readings

Revision ID: 1e9f0b8a7e50
Revises: 4227505c4a72
Create Date: 2026-06-02 11:41:19.993992

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1e9f0b8a7e50"
down_revision: Union[str, None] = "4227505c4a72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "printer_meter_readings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("printer_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("counter_total", sa.Integer(), nullable=False),
        sa.Column("counter_mono", sa.Integer(), nullable=True),
        sa.Column("counter_color", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["printer_id"], ["printers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_printer_meter_readings_printer_ts",
        "printer_meter_readings",
        ["printer_id", "timestamp"],
    )
    op.create_index(
        "ix_print_jobs_timestamp",
        "print_jobs",
        ["timestamp"],
    )


def downgrade() -> None:
    op.drop_index("ix_print_jobs_timestamp", table_name="print_jobs")
    op.drop_index(
        "ix_printer_meter_readings_printer_ts",
        table_name="printer_meter_readings",
    )
    op.drop_table("printer_meter_readings")
