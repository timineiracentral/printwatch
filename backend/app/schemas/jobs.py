"""Schemas Pydantic para /api/v1/jobs (D-01..D-10)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from app.core.config import settings

_API_TZ = ZoneInfo(settings.api_timezone)


class JobOut(BaseModel):
    """Job agregado (D-01..D-06).

    `pages` é COUNT(*) do grupo (D-03). `timestamp` é MIN(timestamp) do
    grupo (D-06) e é serializado em `America/Sao_Paulo` (D-10) mesmo
    que o banco persista em UTC.

    `id` é opcional: presente em `GET /jobs/{id}` (id do PrintJob
    representante do grupo), ausente (null) na listagem agregada.
    """

    model_config = ConfigDict(from_attributes=False)

    id: Optional[int] = None
    printer_id: Optional[int] = None
    printer: str
    username: str
    job_id: int
    job_name: Optional[str] = None
    minute_bucket: Optional[str] = None
    timestamp: datetime
    pages: int
    pages_billable: int = 0
    pages_pending_color: int = 0
    pages_mono: int = 0
    pages_color: int = 0
    estimated_cost: Optional[Decimal] = None
    color_mode: Optional[str] = None
    host_origin: Optional[str] = None
    media: Optional[str] = None
    sides: Optional[str] = None
    outside_policy: bool = False

    @field_serializer("estimated_cost")
    def _serialize_estimated_cost(self, value: Decimal | None) -> float | None:
        if value is None:
            return None
        return float(value.quantize(Decimal("0.0001")))

    @field_serializer("timestamp")
    def _serialize_timestamp_in_sao_paulo(self, value: datetime) -> str:
        """Converte UTC → America/Sao_Paulo e retorna ISO8601 (D-10)."""
        if value.tzinfo is None:
            # Banco salva naive — interpretar como UTC.
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(_API_TZ).isoformat()


class JobFilters(BaseModel):
    """Filtros + paginação para /api/v1/jobs (D-08, D-09).

    `model_config.extra='forbid'` faz com que parâmetros desconhecidos
    retornem HTTP 422, evitando typos silenciosos em integrações.
    """

    model_config = ConfigDict(extra="forbid")

    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=500)
    username: Optional[str] = None
    printer: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    outside_policy: Optional[bool] = None

    @model_validator(mode="after")
    def _validate_date_range(self) -> "JobFilters":
        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValueError("date_from must be <= date_to")
        return self
