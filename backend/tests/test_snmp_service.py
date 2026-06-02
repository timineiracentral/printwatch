"""Testes snmp_service (TONER, Fase 8)."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Printer, PrinterMeterReading, PrinterTonerSnapshot
from app.services import snmp_service


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _add_printer(
    db: Session,
    *,
    snmp_enabled: bool = True,
    ip: str = "192.0.2.50",
) -> Printer:
    now = _utc_now()
    p = Printer(
        display_name="SNMP Test",
        cups_queue_name="snmp-test",
        ip_address=ip,
        snmp_enabled=snmp_enabled,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def test_snmp_disabled_skipped(db_session: Session) -> None:
    p = _add_printer(db_session, snmp_enabled=False)
    asyncio.run(snmp_service.poll_printer_snmp(p, db_session))
    assert db_session.get(PrinterTonerSnapshot, p.id) is None


def test_counter_and_toner_ok(db_session: Session, monkeypatch) -> None:
    p = _add_printer(db_session)

    async def fake_get(ip: str, community: str, oid: str) -> int | None:
        if oid == snmp_service.COUNTER_TOTAL_OID:
            return 5000
        return 40

    monkeypatch.setattr(snmp_service, "snmp_get_int", fake_get)

    async def fake_walk(ip: str, community: str) -> list[int]:
        return [40]

    monkeypatch.setattr(snmp_service, "_walk_supply_levels", fake_walk)

    asyncio.run(snmp_service.poll_printer_snmp(p, db_session))

    snap = db_session.get(PrinterTonerSnapshot, p.id)
    assert snap is not None
    assert snap.status == "ok"
    assert snap.black_pct == 40

    reading = db_session.scalars(
        select(PrinterMeterReading).where(PrinterMeterReading.printer_id == p.id)
    ).first()
    assert reading is not None
    assert reading.source == "snmp"
    assert reading.counter_total == 5000


def test_snmp_failure_unavailable(db_session: Session, monkeypatch) -> None:
    p = _add_printer(db_session)

    async def fail_get(ip: str, community: str, oid: str) -> int | None:
        raise TimeoutError("snmp timeout")

    monkeypatch.setattr(snmp_service, "snmp_get_int", fail_get)

    async def empty_walk(ip: str, community: str) -> list[int]:
        return []

    monkeypatch.setattr(snmp_service, "_walk_supply_levels", empty_walk)

    asyncio.run(snmp_service.poll_printer_snmp(p, db_session))

    snap = db_session.get(PrinterTonerSnapshot, p.id)
    assert snap is not None
    assert snap.status == "unavailable"
    assert snap.black_pct is None
    assert snap.color_pct is None


def test_partial_color(db_session: Session, monkeypatch) -> None:
    p = _add_printer(db_session)

    async def fake_get(ip: str, community: str, oid: str) -> int | None:
        return None

    monkeypatch.setattr(snmp_service, "snmp_get_int", fake_get)

    async def two_levels(ip: str, community: str) -> list[int]:
        return [40, 80]

    monkeypatch.setattr(snmp_service, "_walk_supply_levels", two_levels)

    asyncio.run(snmp_service.poll_printer_snmp(p, db_session))
    snap = db_session.get(PrinterTonerSnapshot, p.id)
    assert snap is not None
    assert snap.partial_color is True
    assert snap.black_pct == 40
    assert snap.color_pct is None


def test_no_community_in_log_strings() -> None:
    from pathlib import Path

    text = Path("app/services/snmp_service.py").read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("#")]
    assert "community=" not in "".join(lines).lower() or "***REDACTED***" in text
