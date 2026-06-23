"""Testes PATCH color_mode por linha (06-03, D-08)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import CostRate, PrintJob


def _setup_pending_line(db: Session) -> tuple[int, str]:
    ts = datetime(2026, 5, 28, 10, 0, 0, tzinfo=timezone.utc).replace(tzinfo=None)
    row = PrintJob(
        printer="epson",
        username="bob",
        job_id=900,
        job_name="doc.pdf",
        timestamp=ts,
        pages=1,
        color_mode=None,
        color_mode_source=None,
    )
    db.add(row)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc).replace(tzinfo=None)
    db.add(
        CostRate(
            rate_mono=Decimal("0.15"),
            rate_color=Decimal("0.60"),
            valid_from=ts,
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()
    db.refresh(row)
    minute = ts.strftime("%Y-%m-%d %H:%M")
    return row.id, minute


def test_patch_null_to_mono_updates_aggregated_job(
    client: TestClient, db_session: Session
) -> None:
    line_id, minute = _setup_pending_line(db_session)

    r_before = client.get(
        "/api/v1/jobs",
        params={"printer": "epson", "username": "bob"},
    )
    assert r_before.json()["items"][0]["pages_mono"] == 0
    assert r_before.json()["items"][0]["estimated_cost"] is None

    patch = client.patch(
        f"/api/v1/jobs/lines/{line_id}/color-mode",
        json={"color_mode": "mono"},
    )
    assert patch.status_code == 200, patch.text
    body = patch.json()
    assert body["color_mode"] == "mono"
    assert body["color_mode_source"] == "manual"

    r_after = client.get(
        "/api/v1/jobs",
        params={"printer": "epson", "username": "bob"},
    )
    job = r_after.json()["items"][0]
    assert job["pages_mono"] == 1
    assert job["pages_pending_color"] == 0
    assert job["pages_billable"] == 1
    assert job["estimated_cost"] == pytest.approx(0.15)

    lines = client.get(
        "/api/v1/jobs/lines",
        params={
            "printer": "epson",
            "username": "bob",
            "job_id": 900,
            "job_name": "doc.pdf",
            "minute_bucket": minute,
        },
    )
    assert lines.status_code == 200
    assert len(lines.json()) == 1


def test_patch_captured_line_sets_manual_source(
    client: TestClient, db_session: Session
) -> None:
    """COLOR-06 D-04: sobrescrever linha captured → color_mode_source=manual."""
    ts = datetime(2026, 5, 28, 11, 0, 0, tzinfo=timezone.utc).replace(tzinfo=None)
    row = PrintJob(
        printer="epson",
        username="carol",
        job_id=901,
        job_name="scan.pdf",
        timestamp=ts,
        pages=1,
        color_mode="color",
        color_mode_source="captured",
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)

    patch = client.patch(
        f"/api/v1/jobs/lines/{row.id}/color-mode",
        json={"color_mode": "mono"},
    )
    assert patch.status_code == 200, patch.text
    body = patch.json()
    assert body["color_mode"] == "mono"
    assert body["color_mode_source"] == "manual"


def test_patch_line_not_found(client: TestClient) -> None:
    r = client.patch(
        "/api/v1/jobs/lines/99999/color-mode",
        json={"color_mode": "color"},
    )
    assert r.status_code == 404


def test_list_lines_missing_query_returns_422(client: TestClient) -> None:
    r = client.get("/api/v1/jobs/lines", params={"printer": "x"})
    assert r.status_code == 422
