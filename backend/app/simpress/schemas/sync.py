"""Schemas Pydantic para /api/v1/simpress/sync (SYNC-04)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SyncStatusRead(BaseModel):
    in_progress: bool


class SyncSummaryRead(BaseModel):
    started_at: datetime
    finished_at: Optional[datetime] = None
    ok: Optional[bool] = None
    contracts_count: int = 0
    contract_codes: list[str] = Field(default_factory=list)
    invoices_upserted: int = 0
    zips_downloaded: int = 0
    cnpj_warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
