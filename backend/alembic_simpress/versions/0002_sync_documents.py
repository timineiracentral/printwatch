"""sync documents — invoices, sync_runs, cnpj warning

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-05 14:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cnpjs",
        sa.Column(
            "invoice_match_warning",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cnpj_id", sa.Integer(), nullable=False),
        sa.Column("contract_code", sa.String(length=64), nullable=False),
        sa.Column("invoice_number", sa.String(length=64), nullable=False),
        sa.Column("cnpj", sa.String(length=14), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("reference", sa.String(length=255), nullable=True),
        sa.Column("zip_token", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cnpj_id"], ["cnpjs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contract_code", "invoice_number", name="uq_invoice_contract_nota"),
        sa.UniqueConstraint("zip_token"),
    )
    op.create_index("ix_invoices_cnpj_id", "invoices", ["cnpj_id"])
    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("ok", sa.Boolean(), nullable=True),
        sa.Column("contracts_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("contract_codes_json", sa.Text(), nullable=True),
        sa.Column("invoices_upserted", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("zips_downloaded", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("cnpj_warnings_json", sa.Text(), nullable=True),
        sa.Column("errors_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("sync_runs")
    op.drop_index("ix_invoices_cnpj_id", table_name="invoices")
    op.drop_table("invoices")
    op.drop_column("cnpjs", "invoice_match_warning")
