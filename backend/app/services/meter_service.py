"""Leituras de contador físico — delta, custo e reconciliação (METER, Fase 7)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.normalize import normalize_printer_name
from app.db.models import Printer, PrinterMeterReading, PrintJob
from app.schemas.meter import MeterReadingCreate, MeterReconciliationRow
from app.services.cost_service import _local_date_to_utc_range, line_cost, rate_at
from app.services.import_service import (
    ImportLineError,
    ImportResult,
    _parse_csv,
    _sanitize_csv_field,
)
from app.services.policy_service import compute_outside_policy, load_policy_context

METER_DIVERGENCE_THRESHOLD_PCT = 0.05

METER_CSV_HEADERS = (
    "printer_code",
    "counter_total",
    "timestamp",
    "counter_mono",
    "counter_color",
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _calendar_date_utc(ts: datetime) -> date:
    tz = ZoneInfo(settings.api_timezone)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(tz).date()


def upsert_snmp_reading_same_day(
    db: Session,
    printer_id: int,
    timestamp: datetime,
    counter_total: int,
    counter_mono: int | None,
    counter_color: int | None,
) -> PrinterMeterReading:
    """D-17: leitura SNMP substitui manual/import no mesmo dia calendário."""
    day = _calendar_date_utc(timestamp)
    for row in list(db.scalars(select(PrinterMeterReading).where(
        PrinterMeterReading.printer_id == printer_id
    ))):
        if row.source in ("manual", "import") and _calendar_date_utc(row.timestamp) == day:
            db.delete(row)

    existing_snmp = [
        r
        for r in db.scalars(
            select(PrinterMeterReading).where(
                PrinterMeterReading.printer_id == printer_id,
                PrinterMeterReading.source == "snmp",
            )
        )
        if _calendar_date_utc(r.timestamp) == day
    ]
    for row in existing_snmp:
        db.delete(row)

    payload = MeterReadingCreate(
        timestamp=timestamp,
        counter_total=counter_total,
        counter_mono=counter_mono,
        counter_color=counter_color,
        source="snmp",
    )
    return create_reading(db, printer_id, payload)


def create_reading(
    db: Session, printer_id: int, payload: MeterReadingCreate
) -> PrinterMeterReading:
    printer = db.get(Printer, printer_id)
    if printer is None or not printer.is_active:
        raise HTTPException(status_code=404, detail="printer not found")

    ts = payload.timestamp
    if ts.tzinfo is not None:
        ts = ts.astimezone(timezone.utc).replace(tzinfo=None)

    row = PrinterMeterReading(
        printer_id=printer_id,
        timestamp=ts,
        counter_total=payload.counter_total,
        counter_mono=payload.counter_mono,
        counter_color=payload.counter_color,
        source=payload.source,
        created_at=_utc_now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_readings(
    db: Session,
    printer_id: int,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 50,
) -> list[PrinterMeterReading]:
    stmt = (
        select(PrinterMeterReading)
        .where(PrinterMeterReading.printer_id == printer_id)
        .order_by(PrinterMeterReading.timestamp.desc())
        .limit(min(limit, 200))
    )
    if date_from is not None:
        start_utc, _ = _local_date_to_utc_range(date_from)
        stmt = stmt.where(PrinterMeterReading.timestamp >= start_utc)
    if date_to is not None:
        _, end_utc = _local_date_to_utc_range(date_to)
        stmt = stmt.where(PrinterMeterReading.timestamp <= end_utc)
    return list(db.scalars(stmt))


def _anchor_readings(
    db: Session,
    printer_id: int,
    start_utc: datetime,
    end_utc: datetime,
) -> tuple[PrinterMeterReading | None, PrinterMeterReading | None, bool]:
    """Leitura inicial/final no intervalo (RESEARCH Pattern 6)."""
    final = db.scalars(
        select(PrinterMeterReading)
        .where(PrinterMeterReading.printer_id == printer_id)
        .where(PrinterMeterReading.timestamp <= end_utc)
        .order_by(PrinterMeterReading.timestamp.desc())
        .limit(1)
    ).first()

    initial = db.scalars(
        select(PrinterMeterReading)
        .where(PrinterMeterReading.printer_id == printer_id)
        .where(PrinterMeterReading.timestamp < start_utc)
        .order_by(PrinterMeterReading.timestamp.desc())
        .limit(1)
    ).first()

    partial = False
    if initial is None:
        initial = db.scalars(
            select(PrinterMeterReading)
            .where(PrinterMeterReading.printer_id == printer_id)
            .where(PrinterMeterReading.timestamp >= start_utc)
            .where(PrinterMeterReading.timestamp <= end_utc)
            .order_by(PrinterMeterReading.timestamp.asc())
            .limit(1)
        ).first()
        partial = initial is not None

    return initial, final, partial


@dataclass
class MeterDelta:
    pages_total: int
    pages_mono: int | None
    pages_color: int | None
    counter_reset: bool = False


def compute_delta(
    initial: PrinterMeterReading | None,
    final: PrinterMeterReading | None,
) -> MeterDelta | None:
    if initial is None or final is None:
        return None

    if final.counter_total < initial.counter_total:
        return MeterDelta(
            pages_total=0,
            pages_mono=0,
            pages_color=0,
            counter_reset=True,
        )

    pages_total = final.counter_total - initial.counter_total
    pages_mono: int | None = None
    pages_color: int | None = None

    if (
        initial.counter_mono is not None
        and initial.counter_color is not None
        and final.counter_mono is not None
        and final.counter_color is not None
    ):
        pages_mono = max(0, final.counter_mono - initial.counter_mono)
        pages_color = max(0, final.counter_color - initial.counter_color)
        pages_total = pages_mono + pages_color

    return MeterDelta(
        pages_total=pages_total,
        pages_mono=pages_mono,
        pages_color=pages_color,
        counter_reset=False,
    )


def pages_jobs_for_printer(
    db: Session,
    printer_id: int,
    date_from: date,
    date_to: date,
) -> int:
    start_utc, _ = _local_date_to_utc_range(date_from)
    _, end_utc = _local_date_to_utc_range(date_to)
    policy_ctx = load_policy_context(db)

    count = 0
    stmt = (
        select(PrintJob)
        .where(PrintJob.printer_id == printer_id)
        .where(PrintJob.timestamp >= start_utc)
        .where(PrintJob.timestamp <= end_utc)
    )
    for job in db.scalars(stmt):
        if compute_outside_policy(policy_ctx, job.username, job.printer_id):
            continue
        if job.color_mode in ("mono", "color"):
            count += 1
    return count


def estimate_meter_cost(
    db: Session,
    printer_id: int,
    delta: MeterDelta,
    date_from: date,
    date_to: date,
) -> tuple[Decimal | None, str | None]:
    """D-25: custo por delta mono/color ou fallback proporcional dos jobs."""
    _, end_utc = _local_date_to_utc_range(date_to)
    rate = rate_at(db, end_utc)
    if rate is None:
        return None, None

    if delta.pages_mono is not None and delta.pages_color is not None:
        cost = (
            Decimal(delta.pages_mono) * Decimal(rate.rate_mono)
            + Decimal(delta.pages_color) * Decimal(rate.rate_color)
        )
        return cost, None

    if delta.pages_total <= 0:
        return Decimal("0"), None

    start_utc, _ = _local_date_to_utc_range(date_from)
    _, end_utc = _local_date_to_utc_range(date_to)
    policy_ctx = load_policy_context(db)
    mono_pages = 0
    color_pages = 0

    stmt = (
        select(PrintJob)
        .where(PrintJob.printer_id == printer_id)
        .where(PrintJob.timestamp >= start_utc)
        .where(PrintJob.timestamp <= end_utc)
    )
    for job in db.scalars(stmt):
        if compute_outside_policy(policy_ctx, job.username, job.printer_id):
            continue
        if job.color_mode == "mono":
            mono_pages += 1
        elif job.color_mode == "color":
            color_pages += 1

    job_total = mono_pages + color_pages
    if job_total == 0:
        cost = line_cost(rate, "mono")
        if cost is None:
            return None, None
        return Decimal(delta.pages_total) * cost, "Custo estimado por tarifa mono (sem jobs no período)"

    mono_ratio = Decimal(mono_pages) / Decimal(job_total)
    color_ratio = Decimal(color_pages) / Decimal(job_total)
    cost = (
        Decimal(delta.pages_total) * mono_ratio * Decimal(rate.rate_mono)
        + Decimal(delta.pages_total) * color_ratio * Decimal(rate.rate_color)
    )
    return cost, "Custo proporcional ao mix mono/color dos jobs no período"


def build_reconciliation(
    db: Session, date_from: date, date_to: date
) -> list[MeterReconciliationRow]:
    start_utc, _ = _local_date_to_utc_range(date_from)
    _, end_utc = _local_date_to_utc_range(date_to)

    rows: list[MeterReconciliationRow] = []
    printers = db.scalars(select(Printer).where(Printer.is_active.is_(True))).all()

    for printer in printers:
        initial, final, partial = _anchor_readings(
            db, printer.id, start_utc, end_utc
        )
        delta = compute_delta(initial, final)
        pages_jobs = pages_jobs_for_printer(db, printer.id, date_from, date_to)

        pages_meter: int | None = None
        cost_meter: Decimal | None = None
        counter_reset = False
        note: str | None = None

        if delta is not None:
            pages_meter = delta.pages_total
            counter_reset = delta.counter_reset
            cost_meter, note = estimate_meter_cost(
                db, printer.id, delta, date_from, date_to
            )

        divergence_pct: float | None = None
        if pages_meter is not None and pages_jobs > 0:
            divergence_pct = round(
                abs(pages_meter - pages_jobs) / pages_jobs * 100.0, 2
            )

        rows.append(
            MeterReconciliationRow(
                printer_id=printer.id,
                printer_name=printer.display_name,
                reading_start=initial.timestamp if initial else None,
                reading_end=final.timestamp if final else None,
                pages_meter=pages_meter,
                cost_meter=cost_meter,
                pages_jobs=pages_jobs,
                divergence_pct=divergence_pct,
                partial_interval=partial,
                counter_reset=counter_reset,
                proportional_cost_note=note,
            )
        )

    return rows


def _resolve_printer(db: Session, printer_code: str) -> Printer | None:
    code = _sanitize_csv_field(printer_code.strip())
    normalized = normalize_printer_name(code)
    if not normalized:
        return None
    for row in db.scalars(select(Printer)):
        if normalize_printer_name(row.cups_queue_name) == normalized:
            return row
        if normalize_printer_name(row.display_name) == normalized:
            return row
    return None


def _parse_timestamp(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def import_readings_csv(db: Session, content: bytes) -> ImportResult:
    result = ImportResult(total=0)
    try:
        parsed = _parse_csv(content, METER_CSV_HEADERS)
    except ValueError as exc:
        result.errors.append(ImportLineError(line=1, message=str(exc)))
        return result

    result.total = len(parsed)
    for line_no, row in parsed:
        try:
            printer = _resolve_printer(db, row["printer_code"])
            if printer is None:
                raise ValueError(
                    f"impressora não encontrada: {row['printer_code']}"
                )

            counter_total = int(row["counter_total"])
            if counter_total < 0:
                raise ValueError("counter_total deve ser >= 0")

            counter_mono = row["counter_mono"].strip()
            counter_color = row["counter_color"].strip()
            mono_val = int(counter_mono) if counter_mono else None
            color_val = int(counter_color) if counter_color else None

            payload = MeterReadingCreate(
                timestamp=_parse_timestamp(row["timestamp"]),
                counter_total=counter_total,
                counter_mono=mono_val,
                counter_color=color_val,
                source="import",
            )
            create_reading(db, printer.id, payload)
            result.created += 1
        except Exception as exc:  # noqa: BLE001 — relatório por linha
            result.errors.append(
                ImportLineError(line=line_no, message=str(exc))
            )

    return result
