"""Schemas Pydantic para /api/v1/departments (D-15, D-16)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    cost_center_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    cost_center_id: Optional[int] = None


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    cost_center_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
