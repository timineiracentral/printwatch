#!/usr/bin/env python3
"""Aplica migrations Alembic no DB_PATH (uso: docker compose exec backend python scripts/migrate_db.py)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    app_root = Path(__file__).resolve().parents[1]
    ini = app_root / "alembic.ini"
    if not ini.is_file():
        print(f"ERROR: {ini} not found", file=sys.stderr)
        return 1
    result = subprocess.run(
        ["alembic", "-c", str(ini), "upgrade", "head"],
        cwd=app_root,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
