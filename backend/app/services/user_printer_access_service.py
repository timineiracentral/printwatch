"""Atribuições N:N usuário ↔ impressora (ACCESS-01..03)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Printer, User, UserPrinterAccess
from app.schemas.user_printer_access import (
    PrinterAccessItem,
    PrinterAccessRead,
    PrinterAccessReplace,
    PrinterUserAccessRead,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user


def _get_printer_or_404(db: Session, printer_id: int) -> Printer:
    printer = db.get(Printer, printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return printer


def _validate_replace_payload(
    db: Session, user: User, payload: PrinterAccessReplace
) -> None:
    if not user.is_active:
        raise HTTPException(status_code=404, detail="user not found")

    seen_printers: set[int] = set()
    default_count = 0
    for item in payload.assignments:
        if item.printer_id in seen_printers:
            raise HTTPException(
                status_code=422, detail="duplicate printer_id in assignments"
            )
        seen_printers.add(item.printer_id)
        if item.is_default:
            default_count += 1
        printer = _get_printer_or_404(db, item.printer_id)
        if not printer.is_active:
            raise HTTPException(
                status_code=404, detail=f"printer {item.printer_id} not found"
            )

    if default_count > 1:
        raise HTTPException(
            status_code=422, detail="only one is_default allowed per user"
        )


def _row_to_read(row: UserPrinterAccess, display_name: str | None = None) -> PrinterAccessRead:
    return PrinterAccessRead(
        id=row.id,
        user_id=row.user_id,
        printer_id=row.printer_id,
        printer_display_name=display_name or (row.printer.display_name if row.printer else None),
        is_default=row.is_default,
        is_active=row.is_active,
    )


def list_for_user(
    db: Session, user_id: int, *, include_inactive: bool = False
) -> list[PrinterAccessRead]:
    _get_user_or_404(db, user_id)
    stmt = (
        select(UserPrinterAccess, Printer.display_name)
        .join(Printer, Printer.id == UserPrinterAccess.printer_id)
        .where(UserPrinterAccess.user_id == user_id)
        .order_by(Printer.display_name.asc())
    )
    if not include_inactive:
        stmt = stmt.where(UserPrinterAccess.is_active.is_(True))
    rows = db.execute(stmt).all()
    return [
        PrinterAccessRead(
            id=access.id,
            user_id=access.user_id,
            printer_id=access.printer_id,
            printer_display_name=display_name,
            is_default=access.is_default,
            is_active=access.is_active,
        )
        for access, display_name in rows
    ]


def replace_for_user(
    db: Session, user_id: int, payload: PrinterAccessReplace
) -> list[PrinterAccessRead]:
    user = _get_user_or_404(db, user_id)
    _validate_replace_payload(db, user, payload)

    now = _utc_now()
    payload_printer_ids = {a.printer_id for a in payload.assignments}
    payload_by_printer = {a.printer_id: a for a in payload.assignments}

    existing = list(
        db.scalars(
            select(UserPrinterAccess).where(UserPrinterAccess.user_id == user_id)
        )
    )
    existing_by_printer = {r.printer_id: r for r in existing}

    for row in existing:
        if row.printer_id not in payload_printer_ids:
            row.is_active = False
            row.is_default = False
            row.updated_at = now

    for item in payload.assignments:
        row = existing_by_printer.get(item.printer_id)
        if row is None:
            db.add(
                UserPrinterAccess(
                    user_id=user_id,
                    printer_id=item.printer_id,
                    is_active=item.is_active,
                    is_default=item.is_default,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            row.is_active = item.is_active
            row.is_default = item.is_default
            row.updated_at = now

    if any(a.is_default for a in payload.assignments):
        default_pid = next(a.printer_id for a in payload.assignments if a.is_default)
        for row in db.scalars(
            select(UserPrinterAccess).where(UserPrinterAccess.user_id == user_id)
        ):
            row.is_default = row.printer_id == default_pid and row.is_active
            row.updated_at = now

    db.commit()
    return list_for_user(db, user_id, include_inactive=True)


def list_users_for_printer(db: Session, printer_id: int) -> list[PrinterUserAccessRead]:
    _get_printer_or_404(db, printer_id)
    stmt = (
        select(User, UserPrinterAccess.is_default)
        .join(UserPrinterAccess, UserPrinterAccess.user_id == User.id)
        .where(
            UserPrinterAccess.printer_id == printer_id,
            UserPrinterAccess.is_active.is_(True),
            User.is_active.is_(True),
        )
        .order_by(User.display_name.asc())
    )
    return [
        PrinterUserAccessRead(
            id=user.id,
            display_name=user.display_name,
            cups_username=user.cups_username,
            is_default=is_default,
        )
        for user, is_default in db.execute(stmt).all()
    ]
