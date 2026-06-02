"""Schemas Pydantic para leituras de contador (METER, Fase 7)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MeterReadingCreate(BaseModel):
    timestamp: datetime
    counter_total: int = Field(..., ge=0)
    counter_mono: Optional[int] = Field(None, ge=0)
    counter_color: Optional[int] = Field(None, ge=0)
    source: Literal["manual", "import"] = "manual"

    @model_validator(mode="after")
    def counter_parts_not_exceed_total(self) -> "MeterReadingCreate":
        mono = self.counter_mono or 0
        color = self.counter_color or 0
        if mono + color > self.counter_total:
            raise ValueError("counter_mono + counter_color cannot exceed counter_total")
        return self


class MeterReadingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    timestamp: datetime
    counter_total: int
    counter_mono: Optional[int] = None
    counter_color: Optional[int] = None
    source: str
    created_at: datetime


class MeterReconciliationRow(BaseModel):
    printer_id: int
    printer_name: str
    reading_start: Optional[datetime] = None
    reading_end: Optional[datetime] = None
    pages_meter: Optional[int] = None
    cost_meter: Optional[Decimal] = None
    pages_jobs: int
    divergence_pct: Optional[float] = None
    partial_interval: bool = False
    counter_reset: bool = False
    proportional_cost_note: Optional[str] = None
