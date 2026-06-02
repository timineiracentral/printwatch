"""Schemas Pydantic para fleet health e toner cache (Fase 8)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

FleetConnectivityStatus = Literal["online", "offline", "unknown"]
FleetStatusSource = Literal["cups", "ping", "unknown"]
TonerSnapshotStatus = Literal["ok", "unavailable"]


class TonerDisplay(BaseModel):
    black_pct: Optional[int] = Field(None, ge=0, le=100)
    color_pct: Optional[int] = Field(None, ge=0, le=100)
    partial_color: bool = False
    status: TonerSnapshotStatus
    checked_at: Optional[datetime] = None

    @model_validator(mode="after")
    def unavailable_clears_pcts(self) -> "TonerDisplay":
        if self.status == "unavailable":
            self.black_pct = None
            self.color_pct = None
        return self


class FleetSummaryCounts(BaseModel):
    online: int = 0
    offline: int = 0
    unknown: int = 0
    total: int = 0


class FleetPrinterRow(BaseModel):
    printer_id: int
    display_name: str
    cups_queue_name: str
    ip_address: Optional[str] = None
    fleet_status: FleetConnectivityStatus
    fleet_source: FleetStatusSource
    last_checked_at: Optional[datetime] = None
    error_message: Optional[str] = None
    snmp_enabled: bool = False
    toner: Optional[TonerDisplay] = None


class FleetListResponse(BaseModel):
    items: list[FleetPrinterRow]
    summary: FleetSummaryCounts


class SnmpTestRequest(BaseModel):
    pass


class SnmpTestResponse(BaseModel):
    ok: bool
    message: str
    counter_total: Optional[int] = None
    black_pct: Optional[int] = Field(None, ge=0, le=100)
    color_pct: Optional[int] = Field(None, ge=0, le=100)
    partial_color: bool = False


class MeterReadingBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    counter_total: int
    counter_mono: Optional[int] = None
    counter_color: Optional[int] = None
    source: str


class FleetPrinterDetail(FleetPrinterRow):
    meter_readings_snmp: list[MeterReadingBrief] = Field(default_factory=list)
