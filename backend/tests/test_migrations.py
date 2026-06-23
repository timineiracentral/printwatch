"""Testes de migration Alembic — schema mestre e printer_id (Fase 5 Plan 01)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

_V1_DDL = (
    """
    CREATE TABLE print_jobs (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        printer VARCHAR(255) NOT NULL,
        username VARCHAR(255) NOT NULL,
        job_id INTEGER NOT NULL,
        timestamp DATETIME NOT NULL,
        pages INTEGER NOT NULL,
        color_mode VARCHAR(50),
        host_origin VARCHAR(255),
        job_name VARCHAR(512),
        media VARCHAR(100),
        sides VARCHAR(50),
        copies INTEGER,
        status VARCHAR(20) NOT NULL DEFAULT 'allowed',
        CONSTRAINT uq_page_log_line UNIQUE (printer, job_id, timestamp, pages)
    )
    """,
    """
    CREATE TABLE capture_state (
        id INTEGER NOT NULL PRIMARY KEY,
        log_path VARCHAR(512) NOT NULL UNIQUE,
        inode INTEGER NOT NULL,
        byte_offset INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE policies (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(255) NOT NULL,
        created_at DATETIME NOT NULL
    )
    """,
)


def _create_v1_schema(db_path: Path) -> None:
    """Bootstrap schema v1.0 (print_jobs sem printer_id) antes do upgrade."""
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        for ddl in _V1_DDL:
            conn.execute(text(ddl))
    engine.dispose()


def _alembic_config(db_path: Path) -> Config:
    os.environ["DB_PATH"] = str(db_path)
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _table_columns(db_path: Path, table: str) -> set[str]:
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    engine.dispose()
    return {row[1] for row in rows}


def _table_exists(db_path: Path, table: str) -> bool:
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=:name"
            ),
            {"name": table},
        ).fetchone()
    engine.dispose()
    return row is not None


@pytest.fixture
def migration_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "migration_test.db"
    _create_v1_schema(db_path)
    return db_path


def test_upgrade_on_empty_db(tmp_path: Path) -> None:
    db_path = tmp_path / "empty.db"
    cfg = _alembic_config(db_path)
    command.upgrade(cfg, "head")

    assert _table_exists(db_path, "print_jobs")
    assert _table_exists(db_path, "printers")
    assert "printer_id" in _table_columns(db_path, "print_jobs")


def test_upgrade_head_creates_master_tables_and_printer_id(migration_db: Path) -> None:
    cfg = _alembic_config(migration_db)
    command.upgrade(cfg, "head")

    for table in ("printers", "departments", "cost_centers", "users"):
        assert _table_exists(migration_db, table), f"missing table {table}"

    cols = _table_columns(migration_db, "print_jobs")
    assert "printer_id" in cols

    engine = create_engine(f"sqlite:///{migration_db}")
    with engine.connect() as conn:
        current = conn.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    engine.dispose()
    assert current == "b7b7e1a82ec4"
    assert _table_exists(migration_db, "user_printer_access")
    assert _table_exists(migration_db, "cost_rates")
    assert _table_exists(migration_db, "printer_meter_readings")
    assert "color_mode_source" in _table_columns(migration_db, "print_jobs")
    assert "color_capability" in _table_columns(migration_db, "printers")


def test_downgrade_user_printer_access_and_reupgrade(migration_db: Path) -> None:
    cfg = _alembic_config(migration_db)
    command.upgrade(cfg, "head")
    assert _table_exists(migration_db, "user_printer_access")

    command.downgrade(cfg, "085a2d5c5767")
    assert not _table_exists(migration_db, "user_printer_access")
    assert _table_exists(migration_db, "printers")

    command.upgrade(cfg, "head")
    assert _table_exists(migration_db, "user_printer_access")


def test_downgrade_cost_rates_and_reupgrade(migration_db: Path) -> None:
    cfg = _alembic_config(migration_db)
    command.upgrade(cfg, "head")
    assert _table_exists(migration_db, "cost_rates")
    assert _table_exists(migration_db, "printer_meter_readings")

    command.downgrade(cfg, "4227505c4a72")
    assert not _table_exists(migration_db, "printer_meter_readings")
    assert _table_exists(migration_db, "cost_rates")

    command.downgrade(cfg, "c4e8f1a92b03")
    assert not _table_exists(migration_db, "cost_rates")

    command.upgrade(cfg, "head")
    assert _table_exists(migration_db, "cost_rates")
    assert _table_exists(migration_db, "printer_meter_readings")


def test_alembic_current_shows_head(migration_db: Path) -> None:
    cfg = _alembic_config(migration_db)
    command.upgrade(cfg, "head")

    engine = create_engine(f"sqlite:///{migration_db}")
    with engine.connect() as conn:
        current = conn.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    engine.dispose()
    assert current == "b7b7e1a82ec4"
