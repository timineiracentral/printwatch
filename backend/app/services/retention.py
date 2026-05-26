from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import PrintJob

logger = logging.getLogger(__name__)


def purge_old_jobs(session: Session, retention_days: int) -> int:
    """Delete print jobs older than retention_days. Returns deleted row count."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=retention_days)
    result = session.execute(
        delete(PrintJob).where(PrintJob.timestamp < cutoff)
    )
    session.commit()
    deleted = result.rowcount
    logger.info(
        "purge_old_jobs: deleted %d record(s) older than %d days",
        deleted,
        retention_days,
    )
    return deleted
