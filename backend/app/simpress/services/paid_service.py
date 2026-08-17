"""Matriz SoT de pagamento — hard (portal/admin) vs soft (WhatsApp Pago).

D-01..D-04, D-07/D-08, D-12/D-15/D-16. Soft never purges ZIP.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.simpress.db.models import Invoice
from app.simpress.services import document_store
from app.simpress.services.invoices_service import CLOSED_STATUSES, OPEN_STATUSES

# ponytail: phone→invoice binding lives in webhook plan (19-04); ceiling = most-recent
# open confirm_cycle×contact claim. Upgrade: reply-to message id if Zap provides it.


@dataclass(frozen=True)
class PaidSignals:
    portal_paid: bool
    admin_settled: bool
    user_paid_pending_recheck: bool
    recheck_after: date | None


def signals_for(invoice: Invoice | Any) -> PaidSignals:
    status = getattr(invoice, "status", None) or ""
    return PaidSignals(
        portal_paid=status in CLOSED_STATUSES,
        admin_settled=bool(getattr(invoice, "admin_settled", False)),
        user_paid_pending_recheck=bool(
            getattr(invoice, "user_paid_pending_recheck", False)
        ),
        recheck_after=getattr(invoice, "recheck_after", None),
    )


def is_hard_stop(s: PaidSignals) -> bool:
    return s.portal_paid or s.admin_settled


def blocks_cadence_drip(s: PaidSignals) -> bool:
    return is_hard_stop(s) or s.user_paid_pending_recheck


def should_purge_zip(s: PaidSignals) -> bool:
    return is_hard_stop(s)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def apply_user_pago(
    db: Session,
    inv: Invoice,
    *,
    contact_id: int,
    click_day_sp: date,
) -> None:
    """Soft-stop only. Sole owner of confirm_cycle increment (D-15)."""
    if inv.admin_settled or inv.status in CLOSED_STATUSES:
        return
    inv.user_paid_pending_recheck = True
    inv.user_paid_at = _utc_now()
    if inv.user_paid_contact_id is None:
        inv.user_paid_contact_id = contact_id
    inv.recheck_after = click_day_sp + timedelta(days=7)
    inv.confirm_cycle = (inv.confirm_cycle or 0) + 1
    inv.updated_at = _utc_now()
    db.add(inv)
    db.commit()
    db.refresh(inv)


def on_portal_paid(
    db: Session,
    inv: Invoice,
    status: str = "Pago",
) -> None:
    """Promote soft→hard: clear recheck, set closed status, purge ZIP (D-03)."""
    if status not in CLOSED_STATUSES:
        raise ValueError("status fechado inválido")
    inv.user_paid_pending_recheck = False
    inv.recheck_after = None
    inv.status = status
    inv.updated_at = _utc_now()
    document_store.delete_zip(db, inv)
    db.refresh(inv)


def admin_settle(db: Session, inv: Invoice) -> None:
    """Hard stop via admin override — purge ZIP without forging portal Pago string."""
    inv.admin_settled = True
    inv.updated_at = _utc_now()
    document_store.delete_zip(db, inv)
    db.refresh(inv)


def admin_resume(db: Session, inv: Invoice) -> None:
    """Clear admin_settled only when portal status still open (D-06)."""
    if inv.status not in OPEN_STATUSES:
        return
    inv.admin_settled = False
    inv.updated_at = _utc_now()
    db.add(inv)
    db.commit()
    db.refresh(inv)
