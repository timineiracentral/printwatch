"""Schemas Pydantic compartilhados entre endpoints."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Resposta paginada genérica (D-08).

    Reutilizada por `/api/v1/jobs` e qualquer endpoint futuro que
    precise de paginação `page/size`. `total` é a contagem agregada
    (jobs após GROUP BY, não linhas brutas do page_log).
    """

    items: list[T]
    total: int
    page: int
    size: int
