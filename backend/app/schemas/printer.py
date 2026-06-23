"""Schemas Pydantic para /api/v1/printers (D-11, D-14, D-18)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PrinterCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    cups_queue_name: str = Field(..., min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    manufacturer_model: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    department_id: Optional[int] = None
    snmp_enabled: bool = False
    snmp_community_override: Optional[str] = Field(
        None,
        max_length=255,
        description="Override opcional da community SNMP; armazenado criptografado em produção",
    )
    color_capability: Optional[Literal["color", "mono_only"]] = None


class PrinterUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    cups_queue_name: Optional[str] = Field(None, min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    manufacturer_model: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    department_id: Optional[int] = None
    snmp_enabled: Optional[bool] = None
    snmp_community_override: Optional[str] = Field(
        None,
        max_length=255,
        description="Override opcional da community SNMP",
    )
    color_capability: Optional[Literal["color", "mono_only"]] = None


class PrinterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    cups_queue_name: str
    ip_address: Optional[str] = None
    manufacturer_model: Optional[str] = None
    location: Optional[str] = None
    department_id: Optional[int] = None
    is_active: bool
    snmp_enabled: bool = False
    snmp_community_override: Optional[str] = Field(
        None,
        description="Mascarado como *** quando configurado (T-08-01)",
    )
    color_capability: Optional[Literal["color", "mono_only"]] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("snmp_community_override")
    def mask_community(self, value: Optional[str]) -> Optional[str]:
        if value:
            return "***"
        return None
