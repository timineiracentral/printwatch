"""Testes unitários fleet_service (FLEET-01/02/03)."""
from __future__ import annotations

from datetime import datetime, timezone

import asyncio

import pytest
from sqlalchemy.orm import Session

from app.db.models import Printer, PrinterFleetStatus
from app.services import fleet_service


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _seed_printer(
    db: Session,
    *,
    display_name: str = "Test Printer",
    cups_queue_name: str = "test-queue",
    ip_address: str | None = "192.0.2.1",
) -> Printer:
    now = _utc_now()
    row = Printer(
        display_name=display_name,
        cups_queue_name=cups_queue_name,
        ip_address=ip_address,
        is_active=True,
        snmp_enabled=False,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_printer_without_ip_unknown(db_session: Session) -> None:
    printer = _seed_printer(db_session, ip_address=None, cups_queue_name="no-ip")
    status, source, err = asyncio.run(
        fleet_service.check_printer_connectivity(printer)
    )
    assert status == "unknown"
    assert source == "unknown"
    assert err is None


def test_cups_idle_online(db_session: Session, monkeypatch) -> None:
    printer = _seed_printer(db_session, cups_queue_name="idle-queue")

    async def _mock_cups(queue: str):
        assert queue == "idle-queue"
        return True, "online"

    monkeypatch.setattr(fleet_service.cups_client, "get_queue_state", _mock_cups)
    status, source, err = asyncio.run(
        fleet_service.check_printer_connectivity(printer)
    )
    assert status == "online"
    assert source == "cups"
    assert err is None


def test_cups_fail_ping_ok(db_session: Session, monkeypatch) -> None:
    printer = _seed_printer(db_session, cups_queue_name="ping-queue")

    async def _mock_cups(queue: str):
        return False, "CUPS down"

    async def _mock_ping(ip: str):
        assert ip == "192.0.2.1"
        return True

    monkeypatch.setattr(fleet_service.cups_client, "get_queue_state", _mock_cups)
    monkeypatch.setattr(fleet_service, "_ping_host", _mock_ping)
    status, source, err = asyncio.run(
        fleet_service.check_printer_connectivity(printer)
    )
    assert status == "online"
    assert source == "ping"
    assert err == "CUPS down"


def test_cups_fail_ping_fail_offline(db_session: Session, monkeypatch) -> None:
    printer = _seed_printer(db_session, cups_queue_name="offline-queue")

    async def _mock_cups(queue: str):
        return False, "timeout"

    async def _mock_ping(ip: str):
        return False

    monkeypatch.setattr(fleet_service.cups_client, "get_queue_state", _mock_cups)
    monkeypatch.setattr(fleet_service, "_ping_host", _mock_ping)
    status, source, err = asyncio.run(
        fleet_service.check_printer_connectivity(printer)
    )
    assert status == "offline"
    assert source == "ping"
    assert err == "timeout"


def test_run_health_cycle_no_ip_unknown(db_session: Session, monkeypatch) -> None:
    _seed_printer(db_session, ip_address=None, cups_queue_name="cycle-no-ip")

    async def _should_not_call(*args, **kwargs):
        raise AssertionError("CUPS should not be called for printer without IP")

    monkeypatch.setattr(fleet_service.cups_client, "get_queue_state", _should_not_call)
    n = fleet_service.run_health_cycle(db_session)
    assert n == 1
    row = db_session.query(PrinterFleetStatus).one()
    assert row.status == "unknown"
    assert row.source == "unknown"


def test_catastrophic_cycle_marks_all_unknown(db_session: Session, monkeypatch) -> None:
    _seed_printer(db_session, cups_queue_name="p1")
    _seed_printer(db_session, cups_queue_name="p2", display_name="P2")

    def _boom(db, printers):
        raise RuntimeError("cycle exploded")

    monkeypatch.setattr(fleet_service, "_run_health_cycle_inner_async", _boom)
    n = fleet_service.run_health_cycle(db_session)
    assert n == 2
    rows = db_session.query(PrinterFleetStatus).all()
    assert len(rows) == 2
    assert all(r.status == "unknown" for r in rows)
    assert all(r.source == "unknown" for r in rows)


def test_build_fleet_list_summary(db_session: Session) -> None:
    printer = _seed_printer(db_session, cups_queue_name="summary-q")
    now = _utc_now()
    db_session.add(
        PrinterFleetStatus(
            printer_id=printer.id,
            status="online",
            source="cups",
            last_checked_at=now,
        )
    )
    db_session.commit()

    result = fleet_service.build_fleet_list(db_session)
    assert result.summary.total == 1
    assert result.summary.online == 1
    assert result.items[0].fleet_status == "online"
