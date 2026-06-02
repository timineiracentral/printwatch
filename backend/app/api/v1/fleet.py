"""GET /api/v1/fleet — overview cache-only (FLEET-03/04)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.fleet import FleetListResponse, FleetPrinterDetail
from app.services import fleet_service

router = APIRouter()


@router.get("", response_model=FleetListResponse)
def list_fleet_endpoint(db: Session = Depends(get_db_dep)) -> FleetListResponse:
    return fleet_service.build_fleet_list(db)


@router.get("/{printer_id}", response_model=FleetPrinterDetail)
def get_fleet_printer_endpoint(
    printer_id: int,
    db: Session = Depends(get_db_dep),
) -> FleetPrinterDetail:
    detail = fleet_service.get_fleet_printer_detail(db, printer_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return detail
