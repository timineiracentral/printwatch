"""Schemas para linhas brutas de print_jobs (correção manual D-08)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.config import settings

_API_TZ = ZoneInfo(settings.api_timezone)


class JobLineFilters(BaseModel):
    """Chaves de agrupamento obrigatórias para GET /jobs/lines."""

    model_config = ConfigDict(extra="forbid")

    printer: str
    username: str
    job_id: int = Field(..., ge=1)
    job_name: Optional[str] = None
    minute_bucket: str = Field(
        ...,
        description="Minuto do grupo em America/Sao_Paulo (YYYY-MM-DD HH:MM)",
    )


class JobLineOut(BaseModel):
    id: int
    timestamp: datetime
    color_mode: Optional[str] = None
    color_mode_source: Optional[str] = None
    pages: int = 1

    @field_serializer("timestamp")
    def _serialize_timestamp_in_sao_paulo(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(_API_TZ).isoformat()


class ColorModePatch(BaseModel):
    color_mode: Literal["mono", "color"]
