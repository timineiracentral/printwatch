"""GET /api/v1/health — health check estendido (D-25).

Mantém `/healthz` (Fase 2) intacto. Este endpoint adiciona
`db_reachable` e adota a semântica:
  - 200 + status="ok"        — db e watcher OK
  - 200 + status="degraded"  — db OK, watcher caiu
  - 503 + status="down"      — db inacessível
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.health import HealthResponse
from app.watcher import status as watcher_status

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    responses={
        503: {"description": "DB inacessível", "model": HealthResponse},
    },
)
def health_endpoint(db: Session = Depends(get_db_dep)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except SQLAlchemyError:
        db_ok = False

    watcher_ok = watcher_status.is_alive()

    if not db_ok:
        return JSONResponse(
            {"status": "down", "db_reachable": False, "watcher_alive": watcher_ok},
            status_code=503,
        )

    status_str = "ok" if watcher_ok else "degraded"
    return HealthResponse(
        status=status_str, db_reachable=True, watcher_alive=watcher_ok
    )
