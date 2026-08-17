"""Schemas Pydantic para /api/v1/simpress/invoices (SYNC-02)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cnpj: str
    invoice_number: str
    status: str
    amount: Decimal
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    reference: Optional[str] = None
    has_zip: bool = False
    admin_settled: bool = False
    user_paid_pending_recheck: bool = False
    recheck_after: Optional[date] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def portal_paid(self) -> bool:
        """Derived from CLOSED portal status — not a DB column (D-04)."""
        return self.status in {"Pago", "Cancelado"}
