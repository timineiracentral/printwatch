"""Fixtures Simpress — env antes do import/reload do app (ISO-01)."""
from __future__ import annotations

import importlib
import os
import sqlite3
import sys
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient


def _reload_app():
    """Recarrega app.main após mudança de env (D-05/D-08)."""
    for mod in list(sys.modules):
        if mod.startswith("app.simpress"):
            del sys.modules[mod]
    import app.main as main_mod

    importlib.reload(main_mod)
    return main_mod


def _build_client(enabled: bool, db_path: str) -> TestClient:
    os.environ["SIMPRESS_ENABLED"] = "true" if enabled else "false"
    os.environ["SIMPRESS_DB_PATH"] = db_path
    main_mod = _reload_app()
    return TestClient(main_mod.app, raise_server_exceptions=False)


@pytest.fixture
def simpress_db_path(tmp_path: Path) -> str:
    return str(tmp_path / "simpress-pytest.db")


@pytest.fixture
def simpress_client_on(simpress_db_path: str) -> Iterator[TestClient]:
    yield _build_client(True, simpress_db_path)


@pytest.fixture
def simpress_client_off(simpress_db_path: str) -> Iterator[TestClient]:
    yield _build_client(False, simpress_db_path)


def core_sqlite_path() -> str:
    return os.environ.get("DB_PATH", "")


def core_table_count(table: str) -> int:
    """Conta linhas em tabela do printwatch.db (core)."""
    path = core_sqlite_path()
    if not path or not os.path.exists(path):
        return 0
    conn = sqlite3.connect(path)
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:
        return 0
    finally:
        conn.close()
