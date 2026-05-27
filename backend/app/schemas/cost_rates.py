"""Schemas Pydantic para /api/v1/cost-rates."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class CostRateCreate(BaseModel):
    rate_mono: Decimal = Field(..., ge=0)
    rate_color: Decimal = Field(..., ge=0)
    valid_from: Optional[datetime] = None


class CostRateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rate_mono: Decimal
    rate_color: Decimal
    valid_from: datetime
    created_at: datetime

    @field_serializer("rate_mono", "rate_color")
    def serialize_decimal(self, value: Decimal) -> str:
        return format(value, "f")
