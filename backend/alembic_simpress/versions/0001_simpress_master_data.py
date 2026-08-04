"""simpress master data tables

Revision ID: 0001
Revises:
Create Date: 2026-08-04 20:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cnpjs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cnpj", sa.String(length=14), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnpj"),
    )
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cnpj_contacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cnpj_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cnpj_id"], ["cnpjs.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnpj_id", "contact_id", name="uq_cnpj_contact"),
    )
    op.create_index("ix_cnpj_contacts_cnpj_id", "cnpj_contacts", ["cnpj_id"])
    op.create_index("ix_cnpj_contacts_contact_id", "cnpj_contacts", ["contact_id"])


def downgrade() -> None:
    op.drop_index("ix_cnpj_contacts_contact_id", table_name="cnpj_contacts")
    op.drop_index("ix_cnpj_contacts_cnpj_id", table_name="cnpj_contacts")
    op.drop_table("cnpj_contacts")
    op.drop_table("contacts")
    op.drop_table("cnpjs")
