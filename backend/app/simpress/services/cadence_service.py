"""Avaliação pura de cadência de lembretes (CAD-01/CAD-04, D-01..D-05)."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.simpress.services.invoices_service import CLOSED_STATUSES

_SP = ZoneInfo("America/Sao_Paulo")


def next_due_stage(
    invoice: Any,
    today: date,
    stage_complete: dict[str, bool] | None = None,
) -> str | None:
    """Retorna o próximo estágio devido ou None.

    ``stage_complete`` reflete claims de envio bem-sucedidos por estágio; a
    conclusão de ``new`` vem de claims (D-02) — esta função não avança a coluna
    ``reminder_stage`` sozinha.
    """
    if stage_complete is None:
        stage_complete = {}

    if invoice.status in CLOSED_STATUSES:
        return None

    launch = invoice.launch_date
    if launch is None:
        return None

    due = _due_date(invoice)

    if invoice.reminder_stage == "reminded_10d":
        if due is not None and today > due:
            return "overdue_urgent"
        return None

    if invoice.reminder_stage == "reminded_5d":
        if today >= launch + timedelta(days=10):
            return "reminded_10d"
        return None

    if invoice.reminder_stage == "new":
        if today >= launch + timedelta(days=5):
            return "reminded_5d"
        if not stage_complete.get("new", False) and today == launch:
            return "new"
        return None

    return None


def _due_date(invoice: Any) -> date | None:
    due_date = getattr(invoice, "due_date", None)
    if due_date is not None:
        return due_date

    due_at = getattr(invoice, "due_at", None)
    if due_at is None:
        return None
    if isinstance(due_at, datetime):
        if due_at.tzinfo is not None:
            return due_at.astimezone(_SP).date()
        return due_at.date()
    if isinstance(due_at, date):
        return due_at
    return None
