"""master_data_tables

Revision ID: 085a2d5c5767
Revises:
Create Date: 2026-05-27 12:03:18.030640

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "085a2d5c5767"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cost_centers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("cost_center_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cost_center_id"], ["cost_centers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "printers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("cups_queue_name", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("manufacturer_model", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cups_queue_name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cups_username", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("cost_center_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cost_center_id"], ["cost_centers.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cups_username"),
    )

    bind = op.get_bind()
    insp = inspect(bind)
    if "print_jobs" not in insp.get_table_names():
        op.create_table(
            "print_jobs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("printer", sa.String(length=255), nullable=False),
            sa.Column("printer_id", sa.Integer(), nullable=True),
            sa.Column("username", sa.String(length=255), nullable=False),
            sa.Column("job_id", sa.Integer(), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("pages", sa.Integer(), nullable=False),
            sa.Column("color_mode", sa.String(length=50), nullable=True),
            sa.Column("host_origin", sa.String(length=255), nullable=True),
            sa.Column("job_name", sa.String(length=512), nullable=True),
            sa.Column("media", sa.String(length=100), nullable=True),
            sa.Column("sides", sa.String(length=50), nullable=True),
            sa.Column("copies", sa.Integer(), nullable=True),
            sa.Column(
                "status",
                sa.String(length=20),
                nullable=False,
                server_default=sa.text("'allowed'"),
            ),
            sa.ForeignKeyConstraint(["printer_id"], ["printers.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "printer", "job_id", "timestamp", "pages", name="uq_page_log_line"
            ),
        )
    else:
        cols = {c["name"] for c in insp.get_columns("print_jobs")}
        if "printer_id" not in cols:
            with op.batch_alter_table("print_jobs") as batch_op:
                batch_op.add_column(
                    sa.Column("printer_id", sa.Integer(), nullable=True)
                )
                batch_op.create_foreign_key(
                    "fk_print_jobs_printer_id",
                    "printers",
                    ["printer_id"],
                    ["id"],
                )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_print_jobs_printer_id_null "
        "ON print_jobs(printer) WHERE printer_id IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_print_jobs_printer_id_null")

    bind = op.get_bind()
    insp = inspect(bind)
    if "print_jobs" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("print_jobs")}
        if "printer_id" in cols:
            with op.batch_alter_table("print_jobs") as batch_op:
                batch_op.drop_constraint("fk_print_jobs_printer_id", type_="foreignkey")
                batch_op.drop_column("printer_id")

    op.drop_table("users")
    op.drop_table("printers")
    op.drop_table("departments")
    op.drop_table("cost_centers")
