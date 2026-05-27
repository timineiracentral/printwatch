"""Cálculo read-time de outside_policy (D-17..D-22)."""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User, UserPrinterAccess


@dataclass
class PolicyContext:
    username_to_user_id: dict[str, int] = field(default_factory=dict)
    user_allowed_printers: dict[int, set[int]] = field(default_factory=dict)


def load_policy_context(db: Session) -> PolicyContext:
    users = db.scalars(select(User).where(User.is_active.is_(True))).all()
    username_to_user_id = {u.cups_username.lower(): u.id for u in users}

    rows = db.scalars(
        select(UserPrinterAccess).where(UserPrinterAccess.is_active.is_(True))
    ).all()
    user_allowed: dict[int, set[int]] = {}
    for row in rows:
        user_allowed.setdefault(row.user_id, set()).add(row.printer_id)

    return PolicyContext(
        username_to_user_id=username_to_user_id,
        user_allowed_printers=user_allowed,
    )


def compute_outside_policy(
    ctx: PolicyContext, username: str, printer_id: int | None
) -> bool:
    """D-20..D-22: true só para user cadastrado com assignments e printer fora do set."""
    if printer_id is None:
        return False

    user_id = ctx.username_to_user_id.get(username.lower())
    if user_id is None:
        return False

    allowed = ctx.user_allowed_printers.get(user_id)
    if not allowed:
        return False

    return printer_id not in allowed
