"""Wave 0 RED — PAID-02 settle/resume HTTP (D-02, D-05, D-06, D-07)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest_simpress import DEFAULT_ZIP_BYTES


def _document_store():
    import importlib

    try:
        return importlib.import_module("app.simpress.services.document_store")
    except ModuleNotFoundError as exc:
        pytest.fail(f"document_store não implementado: {exc}")


def _seed_invoice(db: Any, *, number: str = "NF-SETTLE-01", status: str = "Vencido") -> Any:
    from app.simpress.db.models import Cnpj, Invoice

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cnpj = Cnpj(
        cnpj="11222333000181",
        name="Settle API",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(cnpj)
    db.flush()
    inv = Invoice(
        cnpj_id=cnpj.id,
        contract_code="CTR-SET",
        invoice_number=number,
        cnpj=cnpj.cnpj,
        status=status,
        amount=Decimal("50.00"),
        zip_token=None,
        created_at=now,
        updated_at=now,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    _document_store().save_zip(db, inv, DEFAULT_ZIP_BYTES)
    db.refresh(inv)
    return inv


def test_settle_sets_admin_settled_and_purges_zip(
    simpress_client_on: TestClient,
    simpress_session: Any,
) -> None:
    inv = _seed_invoice(simpress_session)
    assert inv.zip_token

    r = simpress_client_on.post(f"/api/v1/simpress/invoices/{inv.id}/settle")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("admin_settled") is True
    assert body.get("zip_token") in (None, "")

    open_list = simpress_client_on.get("/api/v1/simpress/invoices")
    assert open_list.status_code == 200
    ids = {row["id"] for row in open_list.json()}
    assert inv.id not in ids


def test_settle_works_while_soft_pending(
    simpress_client_on: TestClient,
    simpress_session: Any,
) -> None:
    inv = _seed_invoice(simpress_session, number="NF-SETTLE-SOFT")
    if hasattr(inv, "user_paid_pending_recheck"):
        inv.user_paid_pending_recheck = True
        simpress_session.commit()

    r = simpress_client_on.post(f"/api/v1/simpress/invoices/{inv.id}/settle")
    assert r.status_code == 200, r.text
    assert r.json().get("admin_settled") is True


def test_resume_clears_when_portal_open(
    simpress_client_on: TestClient,
    simpress_session: Any,
) -> None:
    inv = _seed_invoice(simpress_session, number="NF-RESUME-01")
    settle = simpress_client_on.post(f"/api/v1/simpress/invoices/{inv.id}/settle")
    assert settle.status_code == 200, settle.text

    r = simpress_client_on.post(f"/api/v1/simpress/invoices/{inv.id}/resume")
    assert r.status_code == 200, r.text
    assert r.json().get("admin_settled") is False

    open_list = simpress_client_on.get("/api/v1/simpress/invoices")
    ids = {row["id"] for row in open_list.json()}
    assert inv.id in ids


def test_resume_blocked_when_portal_closed(
    simpress_client_on: TestClient,
    simpress_session: Any,
) -> None:
    inv = _seed_invoice(simpress_session, number="NF-RESUME-PAID", status="Pago")
    if hasattr(inv, "admin_settled"):
        inv.admin_settled = True
        simpress_session.commit()

    r = simpress_client_on.post(f"/api/v1/simpress/invoices/{inv.id}/resume")
    assert r.status_code in (400, 409), r.text


def test_settle_unknown_invoice_404(simpress_client_on: TestClient) -> None:
    r = simpress_client_on.post("/api/v1/simpress/invoices/999999/settle")
    assert r.status_code == 404
