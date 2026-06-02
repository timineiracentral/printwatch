"""Testes POST /printers/{id}/snmp-test."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Printer
from app.schemas.fleet import SnmpTestResponse
from app.services import snmp_service


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _seed_printer(db: Session) -> Printer:
    now = _utc_now()
    p = Printer(
        display_name="Fleet SNMP",
        cups_queue_name="fleet-snmp",
        ip_address="192.0.2.55",
        snmp_enabled=True,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def test_snmp_test_ok(client: TestClient, db_session: Session, monkeypatch) -> None:
    p = _seed_printer(db_session)

    async def fake_test(printer_id: int, db: Session):
        return SnmpTestResponse(ok=True, message="SNMP OK", counter_total=100)

    monkeypatch.setattr(snmp_service, "run_snmp_test", fake_test)

    r = client.post(f"/api/v1/printers/{p.id}/snmp-test")
    assert r.status_code == 200
    assert r.json()["ok"] is True
