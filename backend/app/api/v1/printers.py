"""CRUD /api/v1/printers — registry canônico (D-11, D-12, D-14, D-18)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_dep
from app.schemas.printer import PrinterCreate, PrinterRead, PrinterUpdate
from app.services import printers_service
from app.services.matcher_hooks import schedule_match_for_queue

router = APIRouter()


@router.get("", response_model=list[PrinterRead])
def list_printers_endpoint(
    db: Session = Depends(get_db_dep),
    active_only: bool = Query(True, description="Excluir impressoras com is_active=false"),
) -> list[PrinterRead]:
    return printers_service.list_printers(db, active_only=active_only)


@router.post("", response_model=PrinterRead, status_code=201)
def create_printer_endpoint(
    payload: PrinterCreate,
    db: Session = Depends(get_db_dep),
) -> PrinterRead:
    row = printers_service.create_printer(db, payload)
    schedule_match_for_queue(row.cups_queue_name)
    return row


@router.get("/unmapped-queues", response_model=list[str])
def list_unmapped_queues_endpoint(db: Session = Depends(get_db_dep)) -> list[str]:
    return printers_service.list_unmapped_queues(db)


@router.get("/{printer_id}", response_model=PrinterRead)
def get_printer_endpoint(
    printer_id: int,
    db: Session = Depends(get_db_dep),
) -> PrinterRead:
    row = printers_service.get_printer_by_id(db, printer_id)
    if row is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return row


@router.patch("/{printer_id}", response_model=PrinterRead)
def update_printer_endpoint(
    printer_id: int,
    payload: PrinterUpdate,
    db: Session = Depends(get_db_dep),
) -> PrinterRead:
    row = printers_service.update_printer(db, printer_id, payload)
    schedule_match_for_queue(row.cups_queue_name)
    return row


@router.delete("/{printer_id}", response_model=PrinterRead)
def delete_printer_endpoint(
    printer_id: int,
    db: Session = Depends(get_db_dep),
) -> PrinterRead:
    return printers_service.soft_delete_printer(db, printer_id)
