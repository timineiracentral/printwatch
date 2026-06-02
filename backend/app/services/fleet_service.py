"""Fleet health checker — CUPS primário, ping fallback (FLEET-01/02/03)."""
from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Printer, PrinterFleetStatus, PrinterTonerSnapshot
from app.schemas.fleet import (
    FleetListResponse,
    FleetPrinterDetail,
    FleetPrinterRow,
    FleetSummaryCounts,
    MeterReadingBrief,
    TonerDisplay,
)
from app.db.models import PrinterMeterReading
from app.services import cups_client

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upsert_printer_fleet_status(
    session: Session,
    printer_id: int,
    status: str,
    source: str,
    *,
    error_message: str | None = None,
) -> None:
    now = _utc_now()
    row = session.get(PrinterFleetStatus, printer_id)
    if row is None:
        row = PrinterFleetStatus(
            printer_id=printer_id,
            status=status,
            source=source,
            last_checked_at=now,
            error_message=error_message,
        )
        session.add(row)
    else:
        row.status = status
        row.source = source
        row.last_checked_at = now
        row.error_message = error_message
    session.commit()


async def _ping_host(ip_address: str) -> bool:
    if sys.platform == "win32":
        cmd = ["ping", "-n", "1", "-w", "2000", ip_address]
    else:
        cmd = ["ping", "-c", "1", "-W", "2", ip_address]
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            ),
            timeout=5.0,
        )
        await asyncio.wait_for(proc.wait(), timeout=5.0)
        return proc.returncode == 0
    except (asyncio.TimeoutError, OSError):
        return False


async def check_printer_connectivity(
    printer: Printer,
) -> tuple[str, str, str | None]:
    """Retorna (status, source, error_message)."""
    if not printer.ip_address:
        return "unknown", "unknown", None

    cups_ok, cups_result = await cups_client.get_queue_state(printer.cups_queue_name)
    if cups_ok and cups_result in ("online", "offline"):
        return cups_result, "cups", None

    cups_err = cups_result or "CUPS unavailable"
    ping_ok = await _ping_host(printer.ip_address)
    if ping_ok:
        return "online", "ping", cups_err
    return "offline", "ping", cups_err


def run_health_cycle(db: Session) -> int:
    """Executa ciclo de health para impressoras ativas. Retorna contagem processada."""
    printers = list(
        db.scalars(select(Printer).where(Printer.is_active.is_(True))).all()
    )
    if not printers:
        return 0

    try:
        return _run_health_cycle_inner(db, printers)
    except Exception as exc:
        logger.exception("fleet health cycle catastrophic failure")
        msg = str(exc)[:512]
        for printer in printers:
            upsert_printer_fleet_status(
                db,
                printer.id,
                "unknown",
                "unknown",
                error_message=msg,
            )
        return len(printers)


def _run_health_cycle_inner(db: Session, printers: list[Printer]) -> int:
    processed = 0
    for printer in printers:
        try:
            status, source, error_message = asyncio.run(
                check_printer_connectivity(printer)
            )
            upsert_printer_fleet_status(
                db,
                printer.id,
                status,
                source,
                error_message=error_message,
            )
            processed += 1
        except Exception:
            logger.exception(
                "fleet health check failed for printer_id=%s", printer.id
            )
            upsert_printer_fleet_status(
                db,
                printer.id,
                "unknown",
                "unknown",
                error_message="check failed",
            )
            processed += 1
    return processed


def build_fleet_list(db: Session) -> FleetListResponse:
    """Monta overview fleet lendo somente cache (FLEET-03)."""
    printers = list(
        db.scalars(
            select(Printer)
            .where(Printer.is_active.is_(True))
            .order_by(Printer.display_name.asc())
        ).all()
    )

    summary = FleetSummaryCounts(total=len(printers))
    items: list[FleetPrinterRow] = []

    for printer in printers:
        fleet = db.get(PrinterFleetStatus, printer.id)
        toner_row = db.get(PrinterTonerSnapshot, printer.id)

        fleet_status = fleet.status if fleet else "unknown"
        fleet_source = fleet.source if fleet else "unknown"
        last_checked = fleet.last_checked_at if fleet else None
        error_message = fleet.error_message if fleet else None

        toner: TonerDisplay | None = None
        if toner_row is not None:
            toner = TonerDisplay(
                black_pct=toner_row.black_pct if toner_row.status == "ok" else None,
                color_pct=toner_row.color_pct if toner_row.status == "ok" else None,
                partial_color=toner_row.partial_color,
                status=toner_row.status,  # type: ignore[arg-type]
                checked_at=toner_row.checked_at,
            )

        if fleet_status == "online":
            summary.online += 1
        elif fleet_status == "offline":
            summary.offline += 1
        else:
            summary.unknown += 1

        items.append(
            FleetPrinterRow(
                printer_id=printer.id,
                display_name=printer.display_name,
                cups_queue_name=printer.cups_queue_name,
                ip_address=printer.ip_address,
                fleet_status=fleet_status,  # type: ignore[arg-type]
                fleet_source=fleet_source,  # type: ignore[arg-type]
                last_checked_at=last_checked,
                error_message=error_message,
                snmp_enabled=printer.snmp_enabled,
                toner=toner,
            )
        )

    return FleetListResponse(items=items, summary=summary)


def build_fleet_summary_block(db: Session) -> dict:
    """Bloco compacto para GET /manager/summary (D-01) — cache only."""
    data = build_fleet_list(db)
    compact_items = [
        {
            "printer_id": row.printer_id,
            "display_name": row.display_name,
            "fleet_status": row.fleet_status,
            "black_pct": row.toner.black_pct if row.toner else None,
            "toner_status": row.toner.status if row.toner else None,
        }
        for row in data.items[:10]
    ]
    return {
        "counts": data.summary.model_dump(),
        "items": compact_items,
    }


def get_fleet_printer_detail(db: Session, printer_id: int) -> FleetPrinterDetail | None:
    printer = db.get(Printer, printer_id)
    if printer is None or not printer.is_active:
        return None

    fleet_list = build_fleet_list(db)
    row = next((i for i in fleet_list.items if i.printer_id == printer_id), None)
    if row is None:
        return None

    readings = list(
        db.scalars(
            select(PrinterMeterReading)
            .where(
                PrinterMeterReading.printer_id == printer_id,
                PrinterMeterReading.source == "snmp",
            )
            .order_by(PrinterMeterReading.timestamp.desc())
            .limit(5)
        ).all()
    )

    return FleetPrinterDetail(
        **row.model_dump(),
        meter_readings_snmp=[MeterReadingBrief.model_validate(r) for r in readings],
    )
