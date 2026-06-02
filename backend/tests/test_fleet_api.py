"""Testes GET /api/v1/fleet (FLEET-03/04)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Printer, PrinterFleetStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _seed_printer_with_fleet(
    db: Session,
    *,
    status: str = "online",
    source: str = "cups",
) -> Printer:
    now = _utc_now()
    printer = Printer(
        display_name="Fleet Alpha",
        cups_queue_name="fleet-alpha",
        ip_address="192.0.2.50",
        is_active=True,
        snmp_enabled=False,
        created_at=now,
        updated_at=now,
    )
    db.add(printer)
    db.flush()
    db.add(
        PrinterFleetStatus(
            printer_id=printer.id,
            status=status,
            source=source,
            last_checked_at=now,
        )
    )
    db.commit()
    db.refresh(printer)
    return printer


def test_get_fleet_returns_cache(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    _seed_printer_with_fleet(db_session, status="online", source="cups")

    async def _explode(*args, **kwargs):
        raise AssertionError("GET /fleet must not invoke CUPS subprocess")

    monkeypatch.setattr(
        "app.services.cups_client.get_queue_state",
        _explode,
    )

    r = client.get("/api/v1/fleet")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["online"] == 1
    assert body["summary"]["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["fleet_status"] == "online"
    assert body["items"][0]["fleet_source"] == "cups"


def test_get_fleet_empty(client: TestClient, monkeypatch) -> None:
    async def _explode(*args, **kwargs):
        raise AssertionError("GET /fleet must not invoke CUPS subprocess")

    monkeypatch.setattr(
        "app.services.cups_client.get_queue_state",
        _explode,
    )

    r = client.get("/api/v1/fleet")
    assert r.status_code == 200
    assert r.json() == {
        "items": [],
        "summary": {"online": 0, "offline": 0, "unknown": 0, "total": 0},
    }
