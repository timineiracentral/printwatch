"""Schemas Pydantic para /api/v1/users (D-06, D-07, D-17)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    cups_username: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    department_id: int
    cost_center_id: Optional[int] = None


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    department_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cups_username: str
    display_name: str
    department_id: int
    cost_center_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
