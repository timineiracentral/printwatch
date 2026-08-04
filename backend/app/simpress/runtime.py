"""Mount condicional do módulo Simpress (D-05, D-08)."""
from __future__ import annotations

from fastapi import FastAPI

from app.simpress.api.router import simpress_router
from app.simpress.db.base import SimpressBase
from app.simpress.db.session import simpress_engine


def mount_simpress(app: FastAPI) -> None:
    """Bootstrap schema + registra rotas /api/v1/simpress/*."""
    SimpressBase.metadata.create_all(simpress_engine)
    app.include_router(simpress_router, prefix="/api/v1/simpress", tags=["simpress"])
