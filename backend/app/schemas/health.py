"""Schemas Pydantic para /api/v1/health (D-25)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    db_reachable: bool
    watcher_alive: bool
