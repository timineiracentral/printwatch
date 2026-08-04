"""Schemas Pydantic para /api/v1/simpress/health (ISO-02 — sem secrets)."""
from __future__ import annotations

from pydantic import BaseModel


class SimpressHealthResponse(BaseModel):
    status: str
    db_reachable: bool
