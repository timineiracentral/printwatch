"""Service layer para registry de impressoras (D-11, D-14, D-18)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.normalize import normalize_printer_name
from app.db.models import PrintJob, Printer
from app.schemas.printer import PrinterCreate, PrinterUpdate


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalized_key(name: str) -> str:
    norm = normalize_printer_name(name)
    if not norm:
        raise HTTPException(status_code=422, detail="cups_queue_name inválido após normalização")
    return norm


def _validate_snmp(
    snmp_enabled: bool,
    ip_address: Optional[str],
) -> None:
    if snmp_enabled and not ip_address:
        raise HTTPException(
            status_code=422,
            detail="ip_address obrigatório para SNMP",
        )


def _find_duplicate(
    db: Session, normalized: str, *, exclude_id: Optional[int] = None
) -> Optional[Printer]:
    stmt = select(Printer)
    if exclude_id is not None:
        stmt = stmt.where(Printer.id != exclude_id)
    for row in db.scalars(stmt):
        existing = normalize_printer_name(row.cups_queue_name)
        if existing == normalized:
            return row
    return None


def list_printers(db: Session, *, active_only: bool = True) -> list[Printer]:
    stmt = select(Printer).order_by(Printer.display_name.asc())
    if active_only:
        stmt = stmt.where(Printer.is_active.is_(True))
    return list(db.scalars(stmt))


def get_printer_by_id(db: Session, printer_id: int) -> Optional[Printer]:
    return db.get(Printer, printer_id)


def create_printer(db: Session, payload: PrinterCreate) -> Printer:
    normalized = _normalized_key(payload.cups_queue_name)
    if _find_duplicate(db, normalized) is not None:
        raise HTTPException(status_code=409, detail="cups_queue_name já cadastrado")

    _validate_snmp(payload.snmp_enabled, payload.ip_address)

    now = _utc_now()
    row = Printer(
        display_name=payload.display_name.strip(),
        cups_queue_name=normalized,
        ip_address=payload.ip_address,
        manufacturer_model=payload.manufacturer_model,
        location=payload.location,
        department_id=payload.department_id,
        snmp_enabled=payload.snmp_enabled if payload.ip_address else False,
        snmp_community_override=payload.snmp_community_override,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_printer(
    db: Session, printer_id: int, payload: PrinterUpdate
) -> Printer:
    row = get_printer_by_id(db, printer_id)
    if row is None:
        raise HTTPException(status_code=404, detail="printer not found")

    data = payload.model_dump(exclude_unset=True)
    snmp_enabled = data.get("snmp_enabled", row.snmp_enabled)
    ip_address = data.get("ip_address", row.ip_address)
    if "snmp_enabled" in data or "ip_address" in data:
        _validate_snmp(bool(snmp_enabled), ip_address)

    if "cups_queue_name" in data and data["cups_queue_name"] is not None:
        normalized = _normalized_key(data["cups_queue_name"])
        dup = _find_duplicate(db, normalized, exclude_id=printer_id)
        if dup is not None:
            raise HTTPException(status_code=409, detail="cups_queue_name já cadastrado")
        data["cups_queue_name"] = normalized
    if "display_name" in data and data["display_name"] is not None:
        data["display_name"] = data["display_name"].strip()

    final_ip = data.get("ip_address", row.ip_address)
    final_snmp = data.get("snmp_enabled", row.snmp_enabled)
    _validate_snmp(bool(final_snmp), final_ip)
    if "snmp_enabled" in data and not final_ip:
        data["snmp_enabled"] = False

    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = _utc_now()
    db.commit()
    db.refresh(row)
    return row


def soft_delete_printer(db: Session, printer_id: int) -> Printer:
    row = get_printer_by_id(db, printer_id)
    if row is None:
        raise HTTPException(status_code=404, detail="printer not found")
    row.is_active = False
    row.updated_at = _utc_now()
    db.commit()
    db.refresh(row)
    return row


def list_unmapped_queues(db: Session) -> list[str]:
    """Filas DISTINCT em print_jobs sem match no registry (D-12)."""
    job_printers = [
        r[0]
        for r in db.execute(select(PrintJob.printer).distinct()).all()
        if r[0] is not None
    ]
    registry_names = db.scalars(select(Printer.cups_queue_name)).all()
    registry_normalized = {
        n
        for name in registry_names
        if (n := normalize_printer_name(name)) is not None
    }

    unmapped: list[str] = []
    seen: set[str] = set()
    for raw in sorted(job_printers):
        norm = normalize_printer_name(raw)
        if norm is None or norm in registry_normalized or norm in seen:
            continue
        seen.add(norm)
        unmapped.append(norm)
    return unmapped
