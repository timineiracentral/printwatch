"""Integração fleet + manager + snmp-test (Fase 8)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Printer, PrinterFleetStatus, PrinterTonerSnapshot
from app.schemas.fleet import SnmpTestResponse


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _seed(db: Session) -> Printer:
    now = _utc_now()
    p = Printer(
        display_name="Integration",
        cups_queue_name="int-fleet",
        ip_address="192.0.2.60",
        snmp_enabled=True,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(p)
    db.flush()
    db.add(
        PrinterFleetStatus(
            printer_id=p.id,
            status="online",
            source="cups",
            last_checked_at=now,
        )
    )
    db.add(
        PrinterTonerSnapshot(
            printer_id=p.id,
            black_pct=55,
            color_pct=None,
            partial_color=False,
            status="ok",
            checked_at=now,
        )
    )
    db.commit()
    db.refresh(p)
    return p


def test_fleet_and_manager_consistent(
    client: TestClient, db_session: Session
) -> None:
    p = _seed(db_session)

    fleet = client.get("/api/v1/fleet")
    assert fleet.status_code == 200
    item = next(i for i in fleet.json()["items"] if i["printer_id"] == p.id)
    assert item["fleet_status"] == "online"
    assert item["toner"]["black_pct"] == 55

    summary = client.get(
        "/api/v1/manager/summary",
        params={"date_from": "2026-05-01", "date_to": "2026-05-31"},
    )
    assert summary.status_code == 200
    fs = summary.json()["fleet_summary"]
    assert fs["counts"]["online"] >= 1
    compact = next(i for i in fs["items"] if i["printer_id"] == p.id)
    assert compact["fleet_status"] == "online"
    assert compact["black_pct"] == 55


def test_snmp_test_integration(client: TestClient, db_session: Session, monkeypatch) -> None:
    p = _seed(db_session)

    async def fake_test(printer_id: int, db: Session):
        return SnmpTestResponse(ok=True, message="ok")

    monkeypatch.setattr("app.services.snmp_service.run_snmp_test", fake_test)

    r = client.post(f"/api/v1/printers/{p.id}/snmp-test")
    assert r.status_code == 200
    assert r.json()["ok"] is True
