"""Wave 0 RED — OPS-02 / D-16..D-18 via GET /api/v1/simpress/audit."""
from __future__ import annotations

import importlib
import json
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient

_FORBIDDEN = re.compile(
    r"(ZAP_API_KEY|password|secret|api_key|message_body|body_text)",
    re.I,
)


def _audit_service():
    try:
        return importlib.import_module("app.simpress.services.audit_service")
    except ModuleNotFoundError as exc:
        pytest.fail(f"audit_service não implementado: {exc}")


def test_ops02_audit_route_exists(simpress_client_on: TestClient) -> None:
    r = simpress_client_on.get("/api/v1/simpress/audit")
    assert r.status_code == 200, r.text


def test_d16_newest_first_order(simpress_client_on: TestClient) -> None:
    r = simpress_client_on.get("/api/v1/simpress/audit?limit=10")
    assert r.status_code == 200, r.text
    rows = r.json()
    assert isinstance(rows, list)
    if len(rows) >= 2:
        ts = [row.get("created_at") or row.get("timestamp") for row in rows]
        assert ts == sorted(ts, reverse=True), "audit deve ser newest-first"


def test_d17_summary_only_no_secrets_or_body(
    simpress_client_on: TestClient,
) -> None:
    r = simpress_client_on.get("/api/v1/simpress/audit")
    assert r.status_code == 200, r.text
    payload = json.dumps(r.json())
    assert not _FORBIDDEN.search(payload), "audit vazou secret/body"


def test_d17_response_fields_are_summary_shape(
    simpress_client_on: TestClient,
) -> None:
    r = simpress_client_on.get("/api/v1/simpress/audit")
    assert r.status_code == 200, r.text
    rows = r.json()
    if not rows:
        pytest.fail("audit vazio — seed ou service não implementado")
    allowed = {
        "id",
        "channel",
        "part",
        "type",
        "stage",
        "contact_id",
        "contact_name",
        "contact_phone",
        "created_at",
        "timestamp",
        "outcome",
        "http_status",
        "provider_message_id",
        "variant_id",
    }
    for key in rows[0].keys():
        assert key in allowed, f"campo inesperado no audit: {key}"


def test_d18_append_only_no_delete_route(simpress_client_on: TestClient) -> None:
    for method, path in (
        ("delete", "/api/v1/simpress/audit/1"),
        ("post", "/api/v1/simpress/audit"),
        ("put", "/api/v1/simpress/audit/1"),
    ):
        r = getattr(simpress_client_on, method)(path)
        assert r.status_code in (404, 405), f"{method.upper()} audit não deve existir"
