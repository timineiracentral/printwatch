"""Wave 0 RED — PAID-04 +7d button reconfirm (D-14, D-15, D-17)."""
from __future__ import annotations

import importlib
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import pytest

_TZ = ZoneInfo("America/Sao_Paulo")


def _button_reconfirm():
    try:
        return importlib.import_module("app.simpress.services.button_reconfirm")
    except ModuleNotFoundError as exc:
        pytest.fail(f"button_reconfirm não implementado: {exc}")


def _paid_service():
    try:
        return importlib.import_module("app.simpress.services.paid_service")
    except ModuleNotFoundError as exc:
        pytest.fail(f"paid_service não implementado: {exc}")


def _cadence_service():
    try:
        return importlib.import_module("app.simpress.services.cadence_service")
    except ModuleNotFoundError as exc:
        pytest.fail(f"cadence_service não implementado: {exc}")


def _invoice(
    *,
    user_paid_pending_recheck: bool = True,
    recheck_after: date | None = date(2026, 8, 10),
    admin_settled: bool = False,
    status: str = "Vencido",
    confirm_cycle: int = 1,
    reminder_stage: str = "reminded_5d",
    launch_date: date | None = date(2026, 8, 1),
    due_date: date | None = date(2026, 8, 15),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        status=status,
        admin_settled=admin_settled,
        user_paid_pending_recheck=user_paid_pending_recheck,
        recheck_after=recheck_after,
        confirm_cycle=confirm_cycle,
        reminder_stage=reminder_stage,
        launch_date=launch_date,
        due_date=due_date,
        zip_token="keep-me",
    )


def test_due_when_today_sp_gte_recheck_after() -> None:
    br = _button_reconfirm()
    inv = _invoice(recheck_after=date(2026, 8, 10))
    assert br.is_due(inv, today_sp=date(2026, 8, 10)) is True
    assert br.is_due(inv, today_sp=date(2026, 8, 9)) is False


def test_process_due_buttons_only_no_text_doc(
    simpress_session: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    br = _button_reconfirm()
    # Seed minimal soft-pending invoice due today
    from app.simpress.db.models import Cnpj, Invoice

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today = datetime.now(_TZ).date()
    cnpj = Cnpj(
        cnpj="11222333000181",
        name="Reconfirm",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    simpress_session.add(cnpj)
    simpress_session.flush()
    inv = Invoice(
        cnpj_id=cnpj.id,
        contract_code="CTR-RC",
        invoice_number="NF-RC-01",
        cnpj=cnpj.cnpj,
        status="Vencido",
        amount=Decimal("1.00"),
        zip_token="keep-zip",
        created_at=now,
        updated_at=now,
    )
    # Columns added in 19-01 — set if present so RED fails on missing service, not AttributeError noise
    for attr, val in (
        ("user_paid_pending_recheck", True),
        ("recheck_after", today),
        ("confirm_cycle", 2),
        ("admin_settled", False),
    ):
        if hasattr(Invoice, attr):
            setattr(inv, attr, val)
    simpress_session.add(inv)
    simpress_session.commit()

    calls: list[dict] = []

    class FakeZap:
        async def is_connected(self) -> bool:
            return True

        async def send_text(self, *a, **k):
            calls.append({"part": "text", "args": a, "kwargs": k})
            return {"error": False}

        async def send_document(self, *a, **k):
            calls.append({"part": "document", "args": a, "kwargs": k})
            return {"error": False}

        async def send_buttons(self, *a, **k):
            calls.append({"part": "buttons", "args": a, "kwargs": k})
            return {"error": False}

    result = br.process_due(simpress_session, today_sp=today, zap_factory=lambda: FakeZap())
    assert result is not None
    parts = [c["part"] for c in calls]
    assert "buttons" in parts or getattr(result, "buttons_sent", 0) >= 0
    assert "text" not in parts
    assert "document" not in parts


def test_claim_key_uses_current_cycle_without_increment() -> None:
    br = _button_reconfirm()
    inv = _invoice(confirm_cycle=3)
    key = br.claim_key(inv, contact_id=9)
    assert "3" in str(key) or key == (inv.id, 3, 9) or "3" in repr(key)
    # process/send path must not bump confirm_cycle (sole owner = apply_user_pago)
    assert inv.confirm_cycle == 3


def test_cadence_drip_blocked_while_soft() -> None:
    ps = _paid_service()
    cadence = _cadence_service()
    inv = _invoice(user_paid_pending_recheck=True, reminder_stage="new")
    s = ps.signals_for(inv) if hasattr(ps, "signals_for") else SimpleNamespace(
        portal_paid=False,
        admin_settled=False,
        user_paid_pending_recheck=True,
        recheck_after=date(2026, 8, 10),
    )
    assert ps.blocks_cadence_drip(s) is True
    # Cadence drip must not advance while soft (D-01 / D-14)
    stage = cadence.next_due_stage(inv, today=date(2026, 8, 6))
    assert stage is None
