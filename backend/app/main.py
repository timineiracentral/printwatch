from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from watchdog.observers.inotify import InotifyObserver

from app.core.config import settings
from app.db.repository import PrintJobRepository
from app.db.session import SessionLocal
from app.services.tail_reader import TailReader
from app.watcher.checkpoint import CheckpointRepository
from app.watcher.handler import PageLogHandler

logger = logging.getLogger(__name__)

_observer: InotifyObserver | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _observer

    checkpoint_repo = CheckpointRepository(settings.log_path)
    tail_reader = TailReader(settings.log_path, checkpoint_repo)
    repo = PrintJobRepository()
    handler = PageLogHandler(tail_reader, repo, SessionLocal)

    _observer = InotifyObserver()
    _observer.schedule(handler, path="/var/log/cups", recursive=False)
    _observer.daemon = True
    _observer.start()
    logger.info("watcher started: inotify on /var/log/cups (page_log filter)")

    yield

    _observer.stop()
    _observer.join(timeout=5)
    logger.info("watcher stopped")


app = FastAPI(
    title="PrintWatch",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


@app.get("/healthz")
def healthz() -> dict[str, str | bool]:
    alive = _observer is not None and _observer.is_alive()
    return {"status": "ok", "watcher": alive}
