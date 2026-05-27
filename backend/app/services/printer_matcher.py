"""Vínculo assíncrono print_jobs.printer_id (D-01–D-04).

Módulo isolado do watcher — nunca importar em app.watcher.*.
"""
from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.normalize import normalize_printer_name
from app.db.models import PrintJob, Printer

logger = logging.getLogger(__name__)


def resolve_printer_id(session: Session, printer_name: str) -> int | None:
    """Resolve registry id a partir do nome de fila (normalizado)."""
    norm = normalize_printer_name(printer_name)
    if not norm:
        return None
    for row in session.scalars(select(Printer).where(Printer.is_active.is_(True))):
        existing = normalize_printer_name(row.cups_queue_name)
        if existing == norm:
            return row.id
    return None


def match_batch(session: Session, limit: int = 500) -> int:
    """Atualiza até `limit` jobs órfãos; retorna contagem de linhas vinculadas."""
    jobs = list(
        session.scalars(
            select(PrintJob).where(PrintJob.printer_id.is_(None)).limit(limit)
        )
    )
    updated = 0
    for job in jobs:
        pid = resolve_printer_id(session, job.printer)
        if pid is not None:
            job.printer_id = pid
            updated += 1
    if updated:
        session.commit()
    return updated


def match_jobs_for_queue(session: Session, cups_queue_name: str) -> int:
    """On-save (D-03): vincula jobs órfãos cuja fila normalizada coincide."""
    norm_queue = normalize_printer_name(cups_queue_name)
    if not norm_queue:
        return 0
    pid = resolve_printer_id(session, cups_queue_name)
    if pid is None:
        return 0

    updated = 0
    for job in session.scalars(select(PrintJob).where(PrintJob.printer_id.is_(None))):
        if normalize_printer_name(job.printer) == norm_queue:
            job.printer_id = pid
            updated += 1
    if updated:
        session.commit()
    return updated


def count_remaining_null(session: Session) -> int:
    return int(
        session.scalar(
            select(func.count()).select_from(PrintJob).where(PrintJob.printer_id.is_(None))
        )
        or 0
    )


def schedule_match_for_queue(cups_queue_name: str) -> None:
    """Task síncrona para BackgroundTasks — abre sessão própria."""
    from app.db.session import SessionLocal

    session = SessionLocal()
    try:
        n = match_jobs_for_queue(session, cups_queue_name)
        if n:
            logger.info("matcher on-save: %d job(s) linked to queue %r", n, cups_queue_name)
    finally:
        session.close()
