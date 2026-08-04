"""GET /api/v1/simpress/health — probe slim do módulo Simpress (ISO-02)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.simpress.db.session import get_simpress_db
from app.simpress.schemas.health import SimpressHealthResponse

router = APIRouter()


@router.get(
    "",
    response_model=SimpressHealthResponse,
    responses={
        503: {"description": "DB Simpress inacessível", "model": SimpressHealthResponse},
    },
)
def health_endpoint(db: Session = Depends(get_simpress_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except SQLAlchemyError:
        db_ok = False

    if not db_ok:
        return JSONResponse(
            {"status": "down", "db_reachable": False},
            status_code=503,
        )

    return SimpressHealthResponse(status="ok", db_reachable=True)
