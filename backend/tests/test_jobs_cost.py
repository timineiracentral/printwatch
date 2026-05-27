"""Testes JobOut — páginas faturáveis e estimated_cost (06-03)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import CostRate, PrintJob


def _add_rate(db: Session, *, mono: str, color: str, valid_from: datetime) -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc).replace(tzinfo=None)
    db.add(
        CostRate(
            rate_mono=Decimal(mono),
            rate_color=Decimal(color),
            valid_from=valid_from.replace(tzinfo=None)
            if valid_from.tzinfo
            else valid_from,
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()


def _seed_billable_group(db: Session) -> tuple[str, datetime]:
    """Grupo: 2 mono + 1 NULL no mesmo minute_bucket."""
    ts_base = datetime(2026, 5, 27, 15, 30, 0, tzinfo=timezone.utc).replace(tzinfo=None)
    minute = ts_base.strftime("%Y-%m-%d %H:%M")
    for i, mode in enumerate(["mono", "mono", None]):
        db.add(
            PrintJob(
                printer="hp1",
                username="alice",
                job_id=501,
                job_name="report.pdf",
                timestamp=datetime(
                    2026, 5, 27, 15, 30, i * 10, tzinfo=timezone.utc
                ).replace(tzinfo=None),
                pages=1,
                color_mode=mode,
                color_mode_source="captured" if mode else None,
            )
        )
    db.commit()
    return minute, ts_base


def test_job_out_billable_counts(client: TestClient, db_session: Session) -> None:
    minute, _ = _seed_billable_group(db_session)
    r = client.get(
        "/api/v1/jobs",
        params={
            "printer": "hp1",
            "username": "alice",
        },
    )
    assert r.status_code == 200, r.text
    job = r.json()["items"][0]
    assert job["pages"] == 3
    assert job["pages_billable"] == 2
    assert job["pages_pending_color"] == 1
    assert job["pages_mono"] == 2
    assert job["pages_color"] == 0
    assert job["minute_bucket"] == minute


def test_job_out_estimated_cost_with_rates(
    client: TestClient, db_session: Session
) -> None:
    _, ts_base = _seed_billable_group(db_session)
    _add_rate(db_session, mono="0.10", color="0.50", valid_from=ts_base)

    r = client.get("/api/v1/jobs", params={"printer": "hp1"})
    assert r.status_code == 200
    job = r.json()["items"][0]
    assert job["estimated_cost"] == pytest.approx(0.2)


def test_stats_service_has_no_estimated_cost() -> None:
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "app" / "services" / "stats_service.py"
    text = path.read_text(encoding="utf-8")
    assert "estimated_cost" not in text
