"""Schemas Pydantic para /api/v1/simpress/contacts (CNPJ-02)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.simpress.phone import normalize_phone, validate_phone


class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=1, max_length=30)

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        return validate_phone(normalize_phone(v))

    @field_validator("name")
    @classmethod
    def _trim_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("name must be non-empty")
        return s


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, min_length=1, max_length=30)

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_phone(normalize_phone(v))

    @field_validator("name")
    @classmethod
    def _trim_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("name must be non-empty")
        return s


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CnpjIdsReplace(BaseModel):
    cnpj_ids: list[int] = Field(default_factory=list)
