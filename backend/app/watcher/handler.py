from __future__ import annotations

import logging
from typing import Callable

from watchdog.events import FileSystemEventHandler

from app.db.repository import PrintJobRepository
from app.services.parser import parse_page_log_line
from app.services.tail_reader import TailReader

logger = logging.getLogger(__name__)

PAGE_LOG_PATH = "/var/log/cups/page_log"


def pre_process_job(job_dict: dict) -> bool:
    """EXTEND-03: hook de política pré-processamento (MVP sempre permite)."""
    return True


class PageLogHandler(FileSystemEventHandler):
    def __init__(
        self,
        tail_reader: TailReader,
        repo: PrintJobRepository,
        session_factory: Callable,
    ) -> None:
        self._tail = tail_reader
        self._repo = repo
        self._session_factory = session_factory

    def on_modified(self, event) -> None:
        if event.is_directory or event.src_path != PAGE_LOG_PATH:
            return

        for line in self._tail.read_new_lines():
            job_dict = parse_page_log_line(line)
            if job_dict is None:
                logger.debug("linha ignorada: %s", line[:80])
                continue
            if not pre_process_job(job_dict):
                logger.info("job bloqueado pelo hook: job_id=%s", job_dict.get("job_id"))
                continue

            session = self._session_factory()
            try:
                self._repo.insert_job_idempotent(session, job_dict)
            finally:
                session.close()
