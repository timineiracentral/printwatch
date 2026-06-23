"""printer_color_capability

Revision ID: b7b7e1a82ec4
Revises: a3b7c2d4e5f6
Create Date: 2026-06-23 15:56:07.321151

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7b7e1a82ec4"
down_revision: Union[str, None] = "a3b7c2d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "printers",
        sa.Column("color_capability", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("printers", "color_capability")
