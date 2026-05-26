from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import PrintJob
from app.services.retention import purge_old_jobs


@pytest.fixture
def engine_in_memory():
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine_in_memory) -> Session:
    factory = sessionmaker(bind=engine_in_memory)
    db = factory()
    yield db
    db.close()


def _make_job(session: Session, days_ago: int) -> None:
    ts = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    session.add(
        PrintJob(
            printer="p1",
            username="user",
            job_id=1,
            timestamp=ts,
            pages=1,
            status="allowed",
        )
    )
    session.commit()


def test_purge_deletes_record_older_than_retention(session: Session) -> None:
    _make_job(session, days_ago=91)
    deleted = purge_old_jobs(session, retention_days=90)
    assert deleted == 1
    assert session.query(PrintJob).count() == 0


def test_purge_keeps_record_within_retention(session: Session) -> None:
    _make_job(session, days_ago=89)
    deleted = purge_old_jobs(session, retention_days=90)
    assert deleted == 0
    assert session.query(PrintJob).count() == 1


def test_purge_empty_database_returns_zero(session: Session) -> None:
    deleted = purge_old_jobs(session, retention_days=90)
    assert deleted == 0
    assert session.query(PrintJob).count() == 0


def test_purge_deletes_multiple_old_keeps_recent(session: Session) -> None:
    _make_job(session, days_ago=100)
    _make_job(session, days_ago=95)
    _make_job(session, days_ago=10)
    deleted = purge_old_jobs(session, retention_days=90)
    assert deleted == 2
    assert session.query(PrintJob).count() == 1
