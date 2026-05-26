from __future__ import annotations

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.db.models import CaptureState, PrintJob


class PrintJobRepository:
    def insert_job_idempotent(self, session: Session, job_dict: dict) -> None:
        stmt = sqlite_insert(PrintJob).values(**job_dict)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["printer", "job_id", "timestamp", "pages"]
        )
        session.execute(stmt)
        session.commit()

    def get_capture_state(self, session: Session, log_path: str) -> CaptureState | None:
        return session.query(CaptureState).filter_by(log_path=log_path).first()

    def upsert_capture_state(
        self,
        session: Session,
        log_path: str,
        inode: int,
        byte_offset: int,
    ) -> None:
        stmt = sqlite_insert(CaptureState).values(
            log_path=log_path,
            inode=inode,
            byte_offset=byte_offset,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["log_path"],
            set_={"inode": inode, "byte_offset": byte_offset},
        )
        session.execute(stmt)
        session.commit()
