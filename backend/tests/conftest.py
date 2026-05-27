from __future__ import annotations

# DB_PATH default para testes — `app.db.session` faz `create_all(engine)`
# no import top-level; em hosts Windows/Mac (fora do container) o path
# `/app/data/printwatch.db` é inválido. Setar ANTES de qualquer outro
# import garante que `from app.*` funcione sem erro de filesystem.
# Se a env var já existir (CI), respeita-se.
import os
import tempfile

os.environ.setdefault(
    "DB_PATH",
    os.path.join(tempfile.gettempdir(), "printwatch-pytest.db"),
)

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@dataclass
class CaptureState:
    inode: int
    byte_offset: int


class StubStateRepo:
    def __init__(self, state: CaptureState | None = None) -> None:
        self._state = state

    def get(self) -> CaptureState | None:
        return self._state

    def upsert(self, *, inode: int, byte_offset: int) -> None:
        self._state = CaptureState(inode=inode, byte_offset=byte_offset)


@pytest.fixture
def sample_page_log_line() -> str:
    # Usa DOMAIN\\usuario para validar que o parser preserva o formato
    # DOMAIN\user exatamente como recebido do CUPS (D-08).
    # IP usa faixa TEST-NET RFC 5737 (192.0.2.x) — nunca roteável.
    return (
        "test_printer DOMAIN\\usuario 42 [26/May/2026:14:30:00 +0000] "
        "total 3 - 192.0.2.1 relatorio.pdf na_iso_a4_210x297mm one-sided"
    )


@pytest.fixture
def tmp_log_file(tmp_path: Path) -> Path:
    path = tmp_path / "page_log"
    path.write_text("", encoding="utf-8")
    return path


@pytest.fixture
def stub_state_repo() -> StubStateRepo:
    return StubStateRepo()


# ---------------------------------------------------------------------------
# Fixtures para os endpoints da Fase 3 (RESEARCH §9).
# Engine em memória + TestClient com dependency_overrides.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def engine_memory():
    from app.db.base import Base
    from app.db import models  # noqa: F401 — registra modelos no Base

    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def db_session(engine_memory) -> Generator[Session, None, None]:
    """Session function-scope com cleanup das tabelas após cada teste."""
    from app.db import models  # noqa: F401

    SessionLocal = sessionmaker(bind=engine_memory)
    sess = SessionLocal()
    try:
        yield sess
    finally:
        sess.rollback()
        # Limpa dados entre testes — schema persiste session-wide.
        for tbl in reversed(models.Base.metadata.sorted_tables):
            sess.execute(tbl.delete())
        sess.commit()
        sess.close()


@pytest.fixture
def seed_jobs(db_session: Session):
    """Popula DB com 3 jobs distintos (A: 3 págs, B: 1 pág, C: 2 págs).

    Permite validar agregação (D-04) e ordens em testes de API.
    IPs usam TEST-NET RFC 5737 (192.0.2.x).
    """
    from app.db.models import PrintJob

    rows = [
        # Job A — printer=alpha, job_id=100, usr1, 3 páginas
        PrintJob(
            printer="alpha", username="usr1", job_id=100, job_name="A.pdf",
            timestamp=datetime(2026, 5, 26, 13, 0, 0, tzinfo=timezone.utc),
            pages=1, color_mode=None, host_origin="192.0.2.10",
        ),
        PrintJob(
            printer="alpha", username="usr1", job_id=100, job_name="A.pdf",
            timestamp=datetime(2026, 5, 26, 13, 0, 30, tzinfo=timezone.utc),
            pages=2, color_mode=None, host_origin="192.0.2.10",
        ),
        PrintJob(
            printer="alpha", username="usr1", job_id=100, job_name="A.pdf",
            timestamp=datetime(2026, 5, 26, 13, 0, 45, tzinfo=timezone.utc),
            pages=3, color_mode=None, host_origin="192.0.2.10",
        ),
        # Job B — printer=beta, job_id=200, usr2, 1 página
        PrintJob(
            printer="beta", username="usr2", job_id=200, job_name="B.pdf",
            timestamp=datetime(2026, 5, 25, 17, 0, 0, tzinfo=timezone.utc),
            pages=1, color_mode=None, host_origin="192.0.2.20",
        ),
        # Job C — printer=alpha, job_id=300, USR3, 2 páginas
        PrintJob(
            printer="alpha", username="USR3", job_id=300, job_name="C.pdf",
            timestamp=datetime(2026, 5, 26, 14, 30, 0, tzinfo=timezone.utc),
            pages=1, color_mode=None, host_origin="192.0.2.30",
        ),
        PrintJob(
            printer="alpha", username="USR3", job_id=300, job_name="C.pdf",
            timestamp=datetime(2026, 5, 26, 14, 30, 20, tzinfo=timezone.utc),
            pages=2, color_mode=None, host_origin="192.0.2.30",
        ),
    ]
    for r in rows:
        db_session.add(r)
    db_session.commit()
    return rows


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    """TestClient com override de `get_db_dep` → db_session em memória.

    Também registra um FakeObserver no `watcher_status` para que
    `is_alive()` seja determinístico nos testes.
    """
    from app.db.session import get_db_dep
    from app.main import app
    from app.watcher import status as watcher_status

    def _override_db():
        try:
            yield db_session
        finally:
            pass

    class _FakeObserver:
        def __init__(self, alive: bool = True) -> None:
            self._alive = alive

        def is_alive(self) -> bool:
            return self._alive

    watcher_status.register_observer(_FakeObserver(alive=True))
    app.dependency_overrides[get_db_dep] = _override_db
    try:
        # TestClient sem 'with' para evitar lifespan (que tenta abrir
        # InotifyObserver em /var/log/cups — não existe fora de Linux).
        c = TestClient(app)
        yield c
    finally:
        app.dependency_overrides.clear()
        watcher_status.clear()
