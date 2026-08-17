"""Wave 0 RED — PAID-01/02/04 SoT via paid_service (D-01..D-04, D-07/D-08)."""
from __future__ import annotations

import importlib
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from tests.conftest_simpress import DEFAULT_ZIP_BYTES

_TZ = ZoneInfo("America/Sao_Paulo")


def _paid_service():
    try:
        return importlib.import_module("app.simpress.services.paid_service")
    except ModuleNotFoundError as exc:
        pytest.fail(f"paid_service não implementado: {exc}")


def _invoices_service():
    try:
        return importlib.import_module("app.simpress.services.invoices_service")
    except ModuleNotFoundError as exc:
        pytest.fail(f"invoices_service não implementado: {exc}")


def _document_store():
    try:
        return importlib.import_module("app.simpress.services.document_store")
    except ModuleNotFoundError as exc:
        pytest.fail(f"document_store não implementado: {exc}")


def _signals(
    *,
    portal_paid: bool = False,
    admin_settled: bool = False,
    user_paid_pending_recheck: bool = False,
    recheck_after: date | None = None,
) -> Any:
    return SimpleNamespace(
        portal_paid=portal_paid,
        admin_settled=admin_settled,
        user_paid_pending_recheck=user_paid_pending_recheck,
        recheck_after=recheck_after,
    )


def _seed_open_invoice(db: Any, *, zip_bytes: bytes | None = DEFAULT_ZIP_BYTES) -> Any:
    from app.simpress.db.models import Cnpj, Invoice

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cnpj = Cnpj(
        cnpj="11222333000181",
        name="Paid SoT",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(cnpj)
    db.flush()
    inv = Invoice(
        cnpj_id=cnpj.id,
        contract_code="CTR-PAID",
        invoice_number="NF-PAID-01",
        cnpj=cnpj.cnpj,
        status="Vencido",
        amount=Decimal("100.00"),
        zip_token=None,
        created_at=now,
        updated_at=now,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    if zip_bytes is not None:
        _document_store().save_zip(db, inv, zip_bytes)
        db.refresh(inv)
    return inv


def test_portal_paid_hard_stop() -> None:
    ps = _paid_service()
    s = _signals(portal_paid=True)
    assert ps.is_hard_stop(s) is True
    assert ps.should_purge_zip(s) is True
    assert ps.blocks_cadence_drip(s) is True


def test_soft_keeps_zip(
    simpress_session: Any,
    simpress_docs_path: Path,
) -> None:
    ps = _paid_service()
    inv = _seed_open_invoice(simpress_session)
    token_before = inv.zip_token
    assert token_before

    click_day = date(2026, 8, 10)
    ps.apply_user_pago(
        simpress_session,
        inv,
        contact_id=1,
        click_day_sp=click_day,
    )
    simpress_session.refresh(inv)

    assert inv.user_paid_pending_recheck is True
    assert inv.zip_token == token_before
    assert ps.should_purge_zip(ps.signals_for(inv)) is False
    assert (simpress_docs_path / f"{token_before}.zip").is_file()


def test_soft_to_hard_promote_clears_recheck(simpress_session: Any) -> None:
    ps = _paid_service()
    inv = _seed_open_invoice(simpress_session)
    ps.apply_user_pago(
        simpress_session,
        inv,
        contact_id=7,
        click_day_sp=date(2026, 8, 1),
    )
    simpress_session.refresh(inv)
    assert inv.user_paid_pending_recheck is True
    assert inv.recheck_after is not None

    ps.on_portal_paid(simpress_session, inv)
    simpress_session.refresh(inv)

    assert inv.user_paid_pending_recheck is False
    assert inv.recheck_after is None
    s = ps.signals_for(inv)
    assert ps.is_hard_stop(s) is True
    assert ps.should_purge_zip(s) is True


def test_open_list_rules(simpress_session: Any) -> None:
    ps = _paid_service()
    invs = _invoices_service()
    soft = _seed_open_invoice(simpress_session)
    hard = _seed_open_invoice(simpress_session)
    hard.invoice_number = "NF-PAID-HARD"
    simpress_session.commit()

    ps.apply_user_pago(
        simpress_session,
        soft,
        contact_id=1,
        click_day_sp=date(2026, 8, 5),
    )
    ps.admin_settle(simpress_session, hard)
    simpress_session.commit()

    open_ids = {i.id for i in invs.list_open_invoices(simpress_session)}
    assert soft.id in open_ids, "soft-pending permanece na lista aberta (D-08)"
    assert hard.id not in open_ids, "admin_settled sai da lista aberta (D-07)"


def test_apply_user_pago_sole_confirm_cycle_owner(simpress_session: Any) -> None:
    ps = _paid_service()
    inv = _seed_open_invoice(simpress_session)
    before = getattr(inv, "confirm_cycle", 0) or 0

    ps.apply_user_pago(
        simpress_session,
        inv,
        contact_id=3,
        click_day_sp=date(2026, 8, 3),
    )
    simpress_session.refresh(inv)

    assert inv.confirm_cycle == before + 1
    assert inv.recheck_after == date(2026, 8, 3) + __import__("datetime").timedelta(days=7)
    assert inv.user_paid_at is not None
    # D-16: +7 from America/Sao_Paulo calendar click day
    assert inv.recheck_after.tzinfo is None or inv.recheck_after  # date, not datetime


def test_admin_settle_is_hard_and_purges(simpress_session: Any) -> None:
    ps = _paid_service()
    inv = _seed_open_invoice(simpress_session)
    token = inv.zip_token
    ps.admin_settle(simpress_session, inv)
    simpress_session.refresh(inv)

    assert inv.admin_settled is True
    assert inv.zip_token is None
    s = ps.signals_for(inv)
    assert ps.is_hard_stop(s) is True
    assert ps.should_purge_zip(s) is True
    assert token is not None
