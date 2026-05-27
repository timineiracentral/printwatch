"""Schemas para atribuição usuário ↔ impressora (ACCESS-01)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PrinterAccessItem(BaseModel):
    printer_id: int
    is_default: bool = False
    is_active: bool = True


class PrinterAccessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    printer_id: int
    printer_display_name: str | None = None
    is_default: bool
    is_active: bool


class PrinterAccessReplace(BaseModel):
    assignments: list[PrinterAccessItem] = Field(default_factory=list)

    @field_validator("assignments")
    @classmethod
    def _max_assignments(cls, v: list[PrinterAccessItem]) -> list[PrinterAccessItem]:
        if len(v) > 50:
            raise ValueError("assignments cannot exceed 50 items")
        return v


class PrinterUserAccessRead(BaseModel):
    """Vista invertida: usuários com acesso a uma impressora."""

    id: int
    display_name: str
    cups_username: str
    is_default: bool
