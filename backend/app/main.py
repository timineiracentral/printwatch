from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_v1_router
from app.core.config import settings
from app.db.migrations import ensure_indexes, ensure_wal_mode
from app.db.repository import PrintJobRepository
from app.db.session import SessionLocal, engine
from app.services.printer_matcher import match_batch
from app.services.retention import purge_old_jobs
from app.services.tail_reader import TailReader
from app.watcher import status as watcher_status
from app.watcher.checkpoint import CheckpointRepository
from app.watcher.handler import PageLogHandler

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_observer: object | None = None
_matcher_task: asyncio.Task[None] | None = None


async def _matcher_loop() -> None:
    """D-02: batch a cada 60s — só jobs com printer_id IS NULL."""
    while True:
        await asyncio.sleep(60)
        session = SessionLocal()
        try:
            n = match_batch(session)
            if n:
                logger.info("matcher periodic: %d job(s) linked", n)
        except Exception:
            logger.exception("matcher periodic batch failed")
        finally:
            session.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _observer, _matcher_task

    # InotifyObserver é Linux-only — import lazy para permitir dev local no Windows.
    try:
        from watchdog.observers.inotify import InotifyObserver
    except ImportError:
        InotifyObserver = None  # type: ignore[assignment,misc]

    ensure_indexes(engine)
    ensure_wal_mode(engine)

    session = SessionLocal()
    try:
        deleted = purge_old_jobs(session, settings.log_retention_days)
        logger.info(
            "startup purge: %d record(s) deleted (retention %d days)",
            deleted,
            settings.log_retention_days,
        )
    finally:
        session.close()

    if InotifyObserver is not None:
        checkpoint_repo = CheckpointRepository(settings.log_path)
        tail_reader = TailReader(settings.log_path, checkpoint_repo)
        repo = PrintJobRepository()
        handler = PageLogHandler(tail_reader, repo, SessionLocal)

        _observer = InotifyObserver()
        _observer.schedule(handler, path="/var/log/cups", recursive=False)
        _observer.daemon = True
        _observer.start()
        watcher_status.register_observer(_observer)
        logger.info("watcher started: inotify on /var/log/cups (page_log filter)")
    else:
        logger.warning("InotifyObserver unavailable (non-Linux); watcher not started")

    _matcher_task = asyncio.create_task(_matcher_loop())
    logger.info("matcher periodic task started (60s interval)")

    yield

    if _matcher_task is not None:
        _matcher_task.cancel()
        try:
            await _matcher_task
        except asyncio.CancelledError:
            pass
        _matcher_task = None
        logger.info("matcher periodic task stopped")

    if _observer is not None:
        _observer.stop()
        _observer.join(timeout=5)
        watcher_status.clear()
        logger.info("watcher stopped")


_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]

app = FastAPI(
    title="PrintWatch API",
    version="0.3.0",
    docs_url="/api/v1/docs",
    redoc_url=None,
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/healthz")
def healthz() -> dict[str, str | bool]:
    """Probe simplificado para Docker healthcheck (Fase 2, mantido)."""
    return {"status": "ok", "watcher": watcher_status.is_alive()}
