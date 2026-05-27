"""Schemas Pydantic para /api/v1/stats/summary (D-20)."""
from __future__ import annotations

from pydantic import BaseModel


class TopEntry(BaseModel):
    """Item em top_users ou top_printers ordenado por SUM(pages)."""

    name: str
    pages: int


class StatsBucket(BaseModel):
    """Bucket (hoje / mes / total)."""

    jobs: int
    pages: int
    top_users: list[TopEntry]
    top_printers: list[TopEntry]


class StatsSummaryResponse(BaseModel):
    """Resposta de GET /api/v1/stats/summary (D-20)."""

    hoje: StatsBucket
    mes: StatsBucket
    total: StatsBucket
