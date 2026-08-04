"""Schemas Pydantic para /api/v1/simpress/cnpjs (CNPJ-01)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.simpress.cnpj_id import normalize_cnpj, validate_cnpj


class CnpjCreate(BaseModel):
    cnpj: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)

    @field_validator("cnpj")
    @classmethod
    def _validate_cnpj(cls, v: str) -> str:
        return validate_cnpj(normalize_cnpj(v))

    @field_validator("name")
    @classmethod
    def _trim_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("name must be non-empty")
        return s


class CnpjUpdate(BaseModel):
    cnpj: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=255)

    @field_validator("cnpj")
    @classmethod
    def _validate_cnpj(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_cnpj(normalize_cnpj(v))

    @field_validator("name")
    @classmethod
    def _trim_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("name must be non-empty")
        return s


class CnpjRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cnpj: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ContactIdsReplace(BaseModel):
    contact_ids: list[int] = Field(default_factory=list)
