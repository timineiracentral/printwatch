"""Mount condicional do módulo Simpress (D-05, D-08)."""
from __future__ import annotations

import asyncio
import sys

from fastapi import FastAPI

from app.simpress.api.router import simpress_router
from app.simpress.db.base import SimpressBase
from app.simpress.db.session import simpress_engine

_sync_loop_task: asyncio.Task | None = None


def mount_simpress(app: FastAPI) -> None:
    """Bootstrap schema + registra rotas /api/v1/simpress/*."""
    SimpressBase.metadata.create_all(simpress_engine)
    app.include_router(simpress_router, prefix="/api/v1/simpress", tags=["simpress"])

    @app.on_event("startup")
    async def _start_simpress_sync() -> None:
        global _sync_loop_task
        if "pytest" in sys.modules:
            return
        from app.simpress.jobs.daily_sync_loop import daily_sync_loop

        _sync_loop_task = asyncio.create_task(daily_sync_loop())

    @app.on_event("shutdown")
    async def _stop_simpress_sync() -> None:
        global _sync_loop_task
        if _sync_loop_task is not None:
            _sync_loop_task.cancel()
            try:
                await _sync_loop_task
            except asyncio.CancelledError:
                pass
            _sync_loop_task = None
