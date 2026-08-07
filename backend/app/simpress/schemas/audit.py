"""Schemas Pydantic para /api/v1/simpress/audit (OPS-02, D-17)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MessageAuditRead(BaseModel):
    """Resumo append-only — sem body, secrets ou URL de documento."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    outcome: str
    stage: str
    part: str
    channel: str
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    http_status: Optional[int] = None
    variant_id: Optional[str] = None
    provider_message_id: Optional[str] = None
