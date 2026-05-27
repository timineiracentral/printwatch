"""Backfill GAP-02-01: limpa aspas em print_jobs.printer existentes.

Idempotente: rodar 2 vezes seguidas, a segunda execução faz 0 UPDATEs.
Rodar manualmente após deploy do fix:

    docker compose exec backend python -m scripts.backfill_printer_quotes

Não roda no `lifespan` startup (D-22, R-5 do RESEARCH) — migração de
dado deve ser auditável e manual.
"""
from __future__ import annotations

import logging
import sys

from sqlalchemy import select, text, update

from app.db.models import PrintJob
from app.db.session import SessionLocal
from app.services.normalization import normalize_printer_name

logger = logging.getLogger(__name__)

# WHERE clause que isola apenas linhas potencialmente "sujas" — evita
# scan completo após primeira execução. Cobre aspa dupla/simples em
# qualquer extremidade do campo `printer`.
_DIRTY_WHERE = (
    "printer LIKE '\"%' OR printer LIKE '%\"' "
    "OR printer LIKE '''%' OR printer LIKE '%'''"
)


def main() -> int:
    """Executa o backfill. Retorna número de linhas atualizadas (>=0)."""
    session = SessionLocal()
    try:
        before = session.execute(
            text(f"SELECT COUNT(*) FROM print_jobs WHERE {_DIRTY_WHERE}")
        ).scalar_one()

        if before == 0:
            logger.info("backfill: nenhuma linha afetada — nothing to do")
            return 0

        logger.info("backfill: %d linhas com aspas detectadas", before)

        dirty_rows = session.execute(
            select(PrintJob.id, PrintJob.printer).where(
                text(_DIRTY_WHERE)
            )
        ).all()

        fixed = 0
        for row_id, raw in dirty_rows:
            normalized = normalize_printer_name(raw)
            if normalized != raw:
                session.execute(
                    update(PrintJob)
                    .where(PrintJob.id == row_id)
                    .values(printer=normalized)
                )
                fixed += 1

        session.commit()

        after = session.execute(
            text(f"SELECT COUNT(*) FROM print_jobs WHERE {_DIRTY_WHERE}")
        ).scalar_one()

        logger.info(
            "backfill: before=%d after=%d fixed=%d", before, after, fixed
        )

        if after != 0:
            logger.warning(
                "backfill: after=%d != 0 — algumas linhas não foram "
                "normalizadas (normalize_printer_name não removeu o "
                "padrão LIKE). Rever manualmente.",
                after,
            )

        return fixed
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fixed = main()
    sys.exit(0)
