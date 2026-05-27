"""Testes POST /api/v1/admin/backfill-printer-ids (D-04)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import PrintJob, Printer


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def test_backfill_printer_ids_idempotent(client: TestClient, db_session: Session) -> None:
    now = _utc_now()
    db_session.add(
        PrintJob(
            printer="backfill-q",
            printer_id=None,
            username="u1",
            job_id=1,
            timestamp=now,
            pages=1,
        )
    )
    db_session.commit()

    r = client.post("/api/v1/admin/backfill-printer-ids")
    assert r.status_code == 200
    body = r.json()
    assert body["matched_total"] == 0
    assert body["remaining_null"] == 1

    db_session.add(
        Printer(
            display_name="Backfill",
            cups_queue_name="backfill-q",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
    )
    db_session.commit()

    r = client.post("/api/v1/admin/backfill-printer-ids")
    assert r.status_code == 200
    body = r.json()
    assert body["matched_total"] == 1
    assert body["remaining_null"] == 0

    r2 = client.post("/api/v1/admin/backfill-printer-ids")
    assert r2.status_code == 200
    assert r2.json()["matched_total"] == 0
    assert r2.json()["remaining_null"] == 0


def test_backfill_openapi_path(client: TestClient) -> None:
    r = client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    assert "/api/v1/admin/backfill-printer-ids" in r.json()["paths"]
