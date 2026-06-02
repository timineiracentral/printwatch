"""Schemas Pydantic para GET /api/v1/manager/summary (ANAL, Fase 7)."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.meter import MeterReconciliationRow


class TopEntry(BaseModel):
    name: str
    pages: int
    estimated_cost: Optional[Decimal] = None


class PeriodKpi(BaseModel):
    pages_mono: int = 0
    pages_color: int = 0
    pages_billable: int = 0
    pages_pending: int = 0
    estimated_cost: Optional[Decimal] = None
    previous: Optional["PeriodKpi"] = None
    delta_pct_pages: Optional[float] = None
    delta_pct_cost: Optional[float] = None


class ManagerSummaryResponse(BaseModel):
    period: PeriodKpi
    top_users: list[TopEntry] = Field(default_factory=list)
    top_printers: list[TopEntry] = Field(default_factory=list)
    top_departments: list[TopEntry] = Field(default_factory=list)
    meter_reconciliation: list[MeterReconciliationRow] = Field(default_factory=list)
    has_rates: bool = False
    pending_pct: Optional[float] = None
    pending_count: int = 0
