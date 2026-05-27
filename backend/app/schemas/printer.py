"""Schemas Pydantic para /api/v1/printers (D-11, D-14, D-18)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PrinterCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    cups_queue_name: str = Field(..., min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    manufacturer_model: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    department_id: Optional[int] = None


class PrinterUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    cups_queue_name: Optional[str] = Field(None, min_length=1, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    manufacturer_model: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    department_id: Optional[int] = None


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
    created_at: datetime
    updated_at: datetime
