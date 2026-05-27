"""Service layer para usuários (D-06, D-07, D-17)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.services import cost_centers_service, departments_service


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_username(raw: str) -> str:
    s = raw.strip()
    if not s:
        raise HTTPException(status_code=422, detail="cups_username inválido")
    return s


def _validate_department_id(db: Session, department_id: int) -> None:
    dept = departments_service.get_department_by_id(db, department_id)
    if dept is None:
        raise HTTPException(status_code=422, detail="department_id não encontrado")
    if not dept.is_active:
        raise HTTPException(status_code=422, detail="department_id inativo")


def _validate_cost_center_id(db: Session, cost_center_id: Optional[int]) -> None:
    if cost_center_id is None:
        return
    cc = cost_centers_service.get_cost_center_by_id(db, cost_center_id)
    if cc is None:
        raise HTTPException(status_code=422, detail="cost_center_id não encontrado")
    if not cc.is_active:
        raise HTTPException(status_code=422, detail="cost_center_id inativo")


def list_users(
    db: Session,
    *,
    include_inactive: bool = False,
    department_id: Optional[int] = None,
    cost_center_id: Optional[int] = None,
    q: Optional[str] = None,
) -> list[User]:
    stmt = select(User).order_by(User.display_name.asc())
    if not include_inactive:
        stmt = stmt.where(User.is_active.is_(True))
    if department_id is not None:
        stmt = stmt.where(User.department_id == department_id)
    if cost_center_id is not None:
        stmt = stmt.where(User.cost_center_id == cost_center_id)
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(User.cups_username.ilike(term), User.display_name.ilike(term))
        )
    return list(db.scalars(stmt))


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def _find_duplicate_username(
    db: Session, username: str, *, exclude_id: Optional[int] = None
) -> Optional[User]:
    stmt = select(User).where(User.cups_username == username)
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    return db.scalars(stmt).first()


def create_user(db: Session, payload: UserCreate) -> User:
    username = _normalize_username(payload.cups_username)
    if _find_duplicate_username(db, username) is not None:
        raise HTTPException(status_code=409, detail="cups_username já cadastrado")

    _validate_department_id(db, payload.department_id)
    _validate_cost_center_id(db, payload.cost_center_id)

    now = _utc_now()
    row = User(
        cups_username=username,
        display_name=payload.display_name.strip(),
        department_id=payload.department_id,
        cost_center_id=payload.cost_center_id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_user(db: Session, user_id: int, payload: UserUpdate) -> User:
    row = get_user_by_id(db, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")

    data = payload.model_dump(exclude_unset=True)
    if "display_name" in data and data["display_name"] is not None:
        data["display_name"] = data["display_name"].strip()
    if "department_id" in data and data["department_id"] is not None:
        _validate_department_id(db, data["department_id"])
    if "cost_center_id" in data:
        _validate_cost_center_id(db, data["cost_center_id"])

    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = _utc_now()
    db.commit()
    db.refresh(row)
    return row


def soft_delete_user(db: Session, user_id: int) -> User:
    row = get_user_by_id(db, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    row.is_active = False
    row.updated_at = _utc_now()
    db.commit()
    db.refresh(row)
    return row
