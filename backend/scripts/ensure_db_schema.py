#!/usr/bin/env python3
"""Garante colunas/tabelas críticas quando create_all rodou antes do Alembic (deploy legado)."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def _db_path() -> str:
    return os.environ.get("DB_PATH", "/app/data/printwatch.db")


def _ensure_printer_id(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(print_jobs)")}
    if "printer_id" in cols:
        return
    conn.execute(
        "ALTER TABLE print_jobs ADD COLUMN printer_id INTEGER "
        "REFERENCES printers(id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_print_jobs_printer_id_null "
        "ON print_jobs(printer) WHERE printer_id IS NULL"
    )
    conn.commit()
    print("ensure_db_schema: added print_jobs.printer_id", flush=True)


def _ensure_user_printer_access(conn: sqlite3.Connection) -> None:
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if "user_printer_access" in tables:
        return
    conn.executescript(
        """
        CREATE TABLE user_printer_access (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            printer_id INTEGER NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            is_default BOOLEAN NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users (id),
            FOREIGN KEY(printer_id) REFERENCES printers (id),
            CONSTRAINT uq_user_printer UNIQUE (user_id, printer_id)
        );
        CREATE INDEX IF NOT EXISTS ix_user_printer_access_user_id
            ON user_printer_access (user_id);
        CREATE INDEX IF NOT EXISTS ix_user_printer_access_printer_id
            ON user_printer_access (printer_id);
        """
    )
    conn.commit()
    print("ensure_db_schema: created user_printer_access", flush=True)


def _app_root() -> Path:
    here = Path(__file__).resolve().parent
    if (here / "alembic.ini").is_file():
        return here
    return here.parent


def _run_alembic() -> int:
    app_root = _app_root()
    ini = app_root / "alembic.ini"
    if not ini.is_file():
        print("ensure_db_schema: alembic.ini missing, skip alembic", file=sys.stderr)
        return 0
    return subprocess.run(
        ["alembic", "-c", str(ini), "upgrade", "head"],
        cwd=app_root,
        check=False,
    ).returncode


def main() -> int:
    path = _db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "print_jobs" in tables:
            _ensure_printer_id(conn)
        if "users" in tables and "printers" in tables:
            _ensure_user_printer_access(conn)
    finally:
        conn.close()

    code = _run_alembic()
    if code != 0:
        # DB parcialmente migrado via create_all — stamp head se schema já ok
        conn = sqlite3.connect(path)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(print_jobs)")}
        conn.close()
        if "printer_id" in cols:
            root = _app_root()
            subprocess.run(
                [
                    "alembic",
                    "-c",
                    str(root / "alembic.ini"),
                    "stamp",
                    "head",
                ],
                cwd=root,
                check=False,
            )
            print("ensure_db_schema: stamped alembic head after partial DB", flush=True)
            return 0
    return code


if __name__ == "__main__":
    raise SystemExit(main())
