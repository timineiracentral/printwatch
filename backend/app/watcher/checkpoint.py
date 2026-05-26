from __future__ import annotations

from app.db.models import CaptureState
from app.db.repository import PrintJobRepository
from app.db.session import SessionLocal


class CheckpointRepository:
    """Wrapper fino para TailReader — isola checkpoint do ORM."""

    def __init__(self, log_path: str) -> None:
        self._log_path = log_path
        self._repo = PrintJobRepository()

    def get(self) -> CaptureState | None:
        session = SessionLocal()
        try:
            return self._repo.get_capture_state(session, self._log_path)
        finally:
            session.close()

    def upsert(self, *, inode: int, byte_offset: int) -> None:
        session = SessionLocal()
        try:
            self._repo.upsert_capture_state(
                session, self._log_path, inode, byte_offset
            )
        finally:
            session.close()
