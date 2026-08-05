"""Schemas Pydantic para /api/v1/simpress/invoices (SYNC-02)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


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
