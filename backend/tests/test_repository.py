from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import CaptureState, PrintJob
from app.db.repository import PrintJobRepository


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


@pytest.fixture
def repo() -> PrintJobRepository:
    return PrintJobRepository()


@pytest.fixture
def sample_job() -> dict:
    return {
        "printer": "test_printer",
        "username": "DOMAIN\\usuario",
        "job_id": 42,
        "timestamp": datetime(2026, 5, 26, 14, 30, 0, tzinfo=timezone.utc),
        "pages": 3,
        "color_mode": None,
        "host_origin": "192.168.1.10",
        "job_name": "relatorio.pdf",
        "media": "na_iso_a4_210x297mm",
        "sides": "one-sided",
        "copies": None,
        "status": "allowed",
    }


def test_insert_job_idempotent_creates_one_record(
    session: Session, repo: PrintJobRepository, sample_job: dict
) -> None:
    repo.insert_job_idempotent(session, sample_job)
    assert session.query(PrintJob).count() == 1


def test_insert_job_idempotent_duplicate_stays_one_record(
    session: Session, repo: PrintJobRepository, sample_job: dict
) -> None:
    repo.insert_job_idempotent(session, sample_job)
    repo.insert_job_idempotent(session, sample_job)
    assert session.query(PrintJob).count() == 1


def test_get_capture_state_missing_returns_none(
    session: Session, repo: PrintJobRepository
) -> None:
    assert repo.get_capture_state(session, "/var/log/cups/page_log") is None


def test_upsert_capture_state_creates_new(
    session: Session, repo: PrintJobRepository
) -> None:
    log_path = "/var/log/cups/page_log"
    repo.upsert_capture_state(session, log_path, inode=100, byte_offset=0)
    state = repo.get_capture_state(session, log_path)
    assert state is not None
    assert state.inode == 100
    assert state.byte_offset == 0


def test_upsert_capture_state_updates_existing(
    session: Session, repo: PrintJobRepository
) -> None:
    log_path = "/var/log/cups/page_log"
    repo.upsert_capture_state(session, log_path, inode=100, byte_offset=50)
    repo.upsert_capture_state(session, log_path, inode=200, byte_offset=150)
    state = repo.get_capture_state(session, log_path)
    assert state is not None
    assert state.inode == 200
    assert state.byte_offset == 150
    assert session.query(CaptureState).count() == 1
