"""Migrações idempotentes executadas no startup do FastAPI.

D-29 (Fase 3): índices SQLite criados via `CREATE INDEX IF NOT EXISTS`
no `lifespan` ANTES do `purge_old_jobs`. Compatível com volume `db_data`
já populado (Fase 2). Sem ALTER/DROP — apenas CREATE idempotente.

NÃO criar índice funcional sobre `strftime(...)` agora — reavaliar via
EXPLAIN QUERY PLAN se a 50k registros aparecer full scan (D-29).
"""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_INDEX_STATEMENTS = (
    "CREATE INDEX IF NOT EXISTS idx_print_jobs_timestamp "
    "ON print_jobs(timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_print_jobs_username_timestamp "
    "ON print_jobs(username, timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_print_jobs_printer_timestamp "
    "ON print_jobs(printer, timestamp DESC)",
    "CREATE INDEX IF NOT EXISTS idx_print_jobs_job_id "
    "ON print_jobs(job_id)",
)


def ensure_indexes(engine: Engine) -> None:
    """Aplica os 4 índices em uma única transação (idempotente)."""
    with engine.begin() as conn:
        for ddl in _INDEX_STATEMENTS:
            conn.execute(text(ddl))
    logger.info(
        "ensure_indexes: applied %d index DDL statements", len(_INDEX_STATEMENTS)
    )
