"""API leituras de contador — manual, histórico e import CSV (METER)."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.meter import MeterReadingCreate, MeterReadingRead
from app.services import import_service, meter_service
from app.services.import_service import ImportResult
from app.api.v1.import_routes import ImportLineErrorRead, ImportResultRead

router = APIRouter()


@router.post(
    "/printers/{printer_id}/meter-readings",
    response_model=MeterReadingRead,
    status_code=201,
)
def create_meter_reading_endpoint(
    printer_id: int,
    payload: MeterReadingCreate,
    db: Session = Depends(get_db_dep),
) -> MeterReadingRead:
    row = meter_service.create_reading(db, printer_id, payload)
    return MeterReadingRead.model_validate(row)


@router.get(
    "/printers/{printer_id}/meter-readings",
    response_model=list[MeterReadingRead],
)
def list_meter_readings_endpoint(
    printer_id: int,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_dep),
) -> list[MeterReadingRead]:
    rows = meter_service.list_readings(
        db,
        printer_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return [MeterReadingRead.model_validate(r) for r in rows]


@router.post("/import/meter-readings", response_model=ImportResultRead)
async def import_meter_readings_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_dep),
) -> ImportResultRead:
    content = await file.read()
    if len(content) > import_service.MAX_IMPORT_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede limite de {import_service.MAX_IMPORT_BYTES // (1024 * 1024)}MB",
        )
    result: ImportResult = meter_service.import_readings_csv(db, content)
    return ImportResultRead(
        total=result.total,
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        errors=[
            ImportLineErrorRead(line=e.line, message=e.message)
            for e in result.errors
        ],
    )
