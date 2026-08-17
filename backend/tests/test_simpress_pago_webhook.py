"""Wave 0 RED — PAID-03 Zap Pago webhook auth + soft apply (D-12, D-13, D-16)."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "zap_inbound_pago_sample.json"
_WEBHOOK = "/api/v1/simpress/webhooks/zap"
_SECRET = "test-simpress-webhook-secret"
_PHONE = "5511999999999"


def _load_fixture() -> dict:
    data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert data["button"]["label"] == "Pago"
    assert data["from"].isdigit()
    return data


def _seed_open_cycle(db: Any, *, phone: str = _PHONE) -> tuple[Any, Any]:
    from app.simpress.db.models import Cnpj, Contact, Invoice

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cnpj = Cnpj(
        cnpj="11222333000181",
        name="Webhook Pago",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    contact = Contact(
        name="Pagador",
        phone=phone,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add_all([cnpj, contact])
    db.flush()
    inv = Invoice(
        cnpj_id=cnpj.id,
        contract_code="CTR-WH",
        invoice_number="NF-WH-01",
        cnpj=cnpj.cnpj,
        status="Vencido",
        amount=Decimal("10.00"),
        zip_token=None,
        created_at=now,
        updated_at=now,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    db.refresh(contact)
    return inv, contact


def test_fixture_placeholder_exists() -> None:
    assert _FIXTURE.is_file()
    body = _load_fixture()
    assert "Pago" in json.dumps(body)


def test_missing_secret_returns_401(
    simpress_client_on: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SIMPRESS_WEBHOOK_SECRET", _SECRET)
    body = _load_fixture()
    r = simpress_client_on.post(_WEBHOOK, json=body)
    assert r.status_code == 401


def test_wrong_secret_returns_401(
    simpress_client_on: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SIMPRESS_WEBHOOK_SECRET", _SECRET)
    body = _load_fixture()
    r = simpress_client_on.post(
        _WEBHOOK,
        json=body,
        headers={"X-Simpress-Webhook-Secret": "wrong-secret"},
    )
    assert r.status_code == 401


def test_valid_pago_sets_soft_and_recheck_after(
    simpress_client_on: TestClient,
    simpress_session: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SIMPRESS_WEBHOOK_SECRET", _SECRET)
    inv, contact = _seed_open_cycle(simpress_session)
    body = _load_fixture()

    r = simpress_client_on.post(
        _WEBHOOK,
        json=body,
        headers={"X-Simpress-Webhook-Secret": _SECRET},
    )
    assert r.status_code == 200, r.text

    simpress_session.refresh(inv)
    assert inv.user_paid_pending_recheck is True
    assert inv.user_paid_contact_id == contact.id
    assert inv.recheck_after is not None
    # D-16: recheck_after = click calendar day SP + 7
    today_sp = datetime.now(_import_tz()).date()
    assert inv.recheck_after == today_sp + __import__("datetime").timedelta(days=7)
    assert getattr(inv, "confirm_cycle", 0) >= 1


def _import_tz():
    from zoneinfo import ZoneInfo

    return ZoneInfo("America/Sao_Paulo")


def test_first_valid_pago_wins_contact(
    simpress_client_on: TestClient,
    simpress_session: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SIMPRESS_WEBHOOK_SECRET", _SECRET)
    inv, contact = _seed_open_cycle(simpress_session)
    body = _load_fixture()

    r1 = simpress_client_on.post(
        _WEBHOOK,
        json=body,
        headers={"X-Simpress-Webhook-Secret": _SECRET},
    )
    assert r1.status_code == 200, r1.text
    simpress_session.refresh(inv)
    first_contact = inv.user_paid_contact_id
    assert first_contact == contact.id

    # Second click (same phone) must not replace first contact id (D-12 first wins)
    r2 = simpress_client_on.post(
        _WEBHOOK,
        json=body,
        headers={"X-Simpress-Webhook-Secret": _SECRET},
    )
    assert r2.status_code == 200, r2.text
    simpress_session.refresh(inv)
    assert inv.user_paid_contact_id == first_contact
