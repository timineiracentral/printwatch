"""Testes /api/v1/jobs e /api/v1/jobs/{id} (D-01..D-10)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient


def test_list_jobs_empty_returns_page_schema(client: TestClient) -> None:
    r = client.get("/api/v1/jobs")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == {"items": [], "total": 0, "page": 1, "size": 50}


def test_list_jobs_aggregates_by_job(client: TestClient, seed_jobs) -> None:
    r = client.get("/api/v1/jobs")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 3, body
    pages_by_job = {(i["printer"], i["job_id"]): i["pages"] for i in body["items"]}
    assert pages_by_job[("alpha", 100)] == 3
    assert pages_by_job[("beta", 200)] == 1
    assert pages_by_job[("alpha", 300)] == 2


def test_list_jobs_filter_username_case_insensitive(
    client: TestClient, seed_jobs
) -> None:
    r1 = client.get("/api/v1/jobs", params={"username": "USR1"})
    r2 = client.get("/api/v1/jobs", params={"username": "usr1"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["total"] == 1
    assert r2.json()["total"] == 1
    assert r1.json()["items"][0]["job_id"] == 100


def test_list_jobs_filter_printer_exact_match(
    client: TestClient, seed_jobs
) -> None:
    r_lower = client.get("/api/v1/jobs", params={"printer": "alpha"})
    r_upper = client.get("/api/v1/jobs", params={"printer": "Alpha"})
    assert r_lower.json()["total"] == 2
    assert r_upper.json()["total"] == 0


def test_list_jobs_filter_search_in_job_name(
    client: TestClient, seed_jobs
) -> None:
    r = client.get("/api/v1/jobs", params={"search": "B.pdf"})
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["job_id"] == 200


def test_list_jobs_filter_date_range_inclusive(
    client: TestClient, seed_jobs
) -> None:
    # 2026-05-26 em America/Sao_Paulo = de 2026-05-26 03:00 UTC até 2026-05-27 02:59 UTC
    # Job A: 13:00 UTC = 10:00 SP local 26-05 → dentro
    # Job B: 25-05 17:00 UTC = 14:00 SP local 25-05 → FORA
    # Job C: 14:30 UTC = 11:30 SP local 26-05 → dentro
    r = client.get(
        "/api/v1/jobs",
        params={"date_from": "2026-05-26", "date_to": "2026-05-26"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    job_ids = {i["job_id"] for i in body["items"]}
    assert job_ids == {100, 300}


def test_list_jobs_pagination_size_too_large(client: TestClient) -> None:
    r = client.get("/api/v1/jobs", params={"size": 999})
    assert r.status_code == 422


def test_list_jobs_pagination_page_zero(client: TestClient) -> None:
    r = client.get("/api/v1/jobs", params={"page": 0})
    assert r.status_code == 422


def test_list_jobs_invalid_date_range(client: TestClient) -> None:
    r = client.get(
        "/api/v1/jobs",
        params={"date_from": "2026-05-27", "date_to": "2026-05-26"},
    )
    assert r.status_code == 422


def test_list_jobs_extra_query_forbidden(client: TestClient) -> None:
    r = client.get("/api/v1/jobs", params={"unknown_param": "x"})
    assert r.status_code == 422


def test_list_jobs_order_timestamp_desc(
    client: TestClient, seed_jobs
) -> None:
    r = client.get("/api/v1/jobs")
    items = r.json()["items"]
    timestamps = [i["timestamp"] for i in items]
    assert timestamps == sorted(timestamps, reverse=True)


def test_list_jobs_timestamp_in_sao_paulo(
    client: TestClient, seed_jobs
) -> None:
    r = client.get("/api/v1/jobs")
    items = r.json()["items"]
    assert items, "esperado >= 1 job"
    # America/Sao_Paulo = UTC-3 (sem DST atual). Offset "-03:00" no ISO.
    assert "-03:00" in items[0]["timestamp"], items[0]


def test_get_job_by_id_returns_aggregated(
    client: TestClient, seed_jobs, db_session
) -> None:
    from app.db.models import PrintJob

    # Pegar qualquer PrintJob.id do job A (espera-se pages=3 agregado).
    any_row_job_a = (
        db_session.query(PrintJob).filter(PrintJob.job_id == 100).first()
    )
    assert any_row_job_a is not None
    r = client.get(f"/api/v1/jobs/{any_row_job_a.id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["job_id"] == 100
    assert body["pages"] == 3
    assert body["printer"] == "alpha"
    assert body["id"] == any_row_job_a.id


def test_get_job_by_id_not_found(client: TestClient) -> None:
    r = client.get("/api/v1/jobs/999999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"]


def test_jobs_list_has_manual_correction_aggregate(
    client: TestClient, db_session
) -> None:
    from app.db.models import PrintJob

    ts = datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc)
    manual_rows = [
        PrintJob(
            printer="gamma",
            username="usr4",
            job_id=401,
            job_name="Manual.pdf",
            timestamp=ts,
            pages=1,
            color_mode="mono",
            color_mode_source="manual",
            host_origin="192.0.2.40",
        ),
        PrintJob(
            printer="gamma",
            username="usr4",
            job_id=401,
            job_name="Manual.pdf",
            timestamp=datetime(2026, 5, 27, 10, 0, 15, tzinfo=timezone.utc),
            pages=1,
            color_mode="color",
            color_mode_source="captured",
            host_origin="192.0.2.40",
        ),
    ]
    captured_only = PrintJob(
        printer="gamma",
        username="usr5",
        job_id=402,
        job_name="Captured.pdf",
        timestamp=ts,
        pages=1,
        color_mode="color",
        color_mode_source="captured",
        host_origin="192.0.2.41",
    )
    for row in [*manual_rows, captured_only]:
        db_session.add(row)
    db_session.commit()

    r = client.get("/api/v1/jobs", params={"printer": "gamma"})
    assert r.status_code == 200, r.text
    by_job = {i["job_id"]: i for i in r.json()["items"]}
    assert by_job[401]["has_manual_correction"] is True
    assert by_job[402]["has_manual_correction"] is False


def test_job_detail_has_manual_correction(
    client: TestClient, db_session
) -> None:
    from app.db.models import PrintJob

    ts = datetime(2026, 5, 27, 11, 0, 0, tzinfo=timezone.utc)
    manual_row = PrintJob(
        printer="delta",
        username="usr6",
        job_id=501,
        job_name="DetailManual.pdf",
        timestamp=ts,
        pages=1,
        color_mode="mono",
        color_mode_source="manual",
        host_origin="192.0.2.50",
    )
    captured_row = PrintJob(
        printer="delta",
        username="usr7",
        job_id=502,
        job_name="DetailCaptured.pdf",
        timestamp=ts,
        pages=1,
        color_mode="color",
        color_mode_source="captured",
        host_origin="192.0.2.51",
    )
    db_session.add(manual_row)
    db_session.add(captured_row)
    db_session.commit()

    r_manual = client.get(f"/api/v1/jobs/{manual_row.id}")
    assert r_manual.status_code == 200, r_manual.text
    assert r_manual.json()["has_manual_correction"] is True

    r_captured = client.get(f"/api/v1/jobs/{captured_row.id}")
    assert r_captured.status_code == 200, r_captured.text
    assert r_captured.json()["has_manual_correction"] is False
