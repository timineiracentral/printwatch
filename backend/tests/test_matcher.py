"""Testes printer_matcher (D-01–D-04, INV-04, INV-05)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.db.models import PrintJob, Printer
from app.services.printer_matcher import (
    match_batch,
    match_jobs_for_queue,
    resolve_printer_id,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def orphan_jobs_and_printer(db_session: Session):
    """2 jobs órfãos + 1 impressora no registry (fila lab-printer)."""
    now = _utc_now()
    printer = Printer(
        display_name="Lab",
        cups_queue_name="lab-printer",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(printer)
    db_session.flush()

    jobs = [
        PrintJob(
            printer="lab-printer",
            printer_id=None,
            username="u1",
            job_id=1,
            timestamp=now,
            pages=1,
        ),
        PrintJob(
            printer='"lab-printer"',
            printer_id=None,
            username="u2",
            job_id=2,
            timestamp=now,
            pages=1,
        ),
        PrintJob(
            printer="unknown-queue",
            printer_id=None,
            username="u3",
            job_id=3,
            timestamp=now,
            pages=1,
        ),
    ]
    for j in jobs:
        db_session.add(j)
    db_session.commit()
    return printer, jobs


def test_resolve_printer_id(db_session: Session, orphan_jobs_and_printer) -> None:
    printer, _ = orphan_jobs_and_printer
    assert resolve_printer_id(db_session, '"lab-printer"') == printer.id
    assert resolve_printer_id(db_session, "missing") is None


def test_match_batch_links_orphans(db_session: Session, orphan_jobs_and_printer) -> None:
    printer, jobs = orphan_jobs_and_printer
    n = match_batch(db_session, limit=500)
    assert n == 2

    db_session.refresh(jobs[0])
    db_session.refresh(jobs[1])
    db_session.refresh(jobs[2])
    assert jobs[0].printer_id == printer.id
    assert jobs[1].printer_id == printer.id
    assert jobs[2].printer_id is None

    assert match_batch(db_session) == 0


def test_match_jobs_for_queue_on_save(db_session: Session) -> None:
    now = _utc_now()
    db_session.add(
        PrintJob(
            printer="new-queue",
            printer_id=None,
            username="u1",
            job_id=10,
            timestamp=now,
            pages=1,
        )
    )
    db_session.commit()

    assert match_jobs_for_queue(db_session, "new-queue") == 0

    printer = Printer(
        display_name="New",
        cups_queue_name="new-queue",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(printer)
    db_session.commit()

    assert match_jobs_for_queue(db_session, "new-queue") == 1
    assert match_jobs_for_queue(db_session, "new-queue") == 0
