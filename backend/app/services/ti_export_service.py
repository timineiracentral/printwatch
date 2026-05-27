"""Export roteiro TI por usuário (D-13..D-16)."""
from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Printer, User, UserPrinterAccess


def _build_ipp_url(printer: Printer) -> str | None:
    if not printer.ip_address:
        return None
    return f"ipp://{printer.ip_address}/printers/{printer.cups_queue_name}"


def build_ti_export_rows(db: Session, user_id: int) -> list[dict[str, Any]]:
    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .options(joinedload(User.department))
    )
    if user is None or not user.is_active:
        raise HTTPException(status_code=404, detail="user not found")

    stmt = (
        select(UserPrinterAccess)
        .where(
            UserPrinterAccess.user_id == user_id,
            UserPrinterAccess.is_active.is_(True),
        )
        .options(
            joinedload(UserPrinterAccess.printer).joinedload(Printer.department),
            joinedload(UserPrinterAccess.user).joinedload(User.department),
        )
    )
    rows = db.scalars(stmt).unique().all()

    dept_name = user.department.name if user.department else None
    result: list[dict[str, Any]] = []
    for access in rows:
        printer = access.printer
        if printer is None or not printer.is_active:
            continue
        result.append(
            {
                "display_name": user.display_name,
                "username": user.cups_username,
                "printer_display_name": printer.display_name,
                "cups_queue_name": printer.cups_queue_name,
                "ipp_url": _build_ipp_url(printer),
                "is_default": access.is_default,
                "department": dept_name,
                "location": printer.location,
            }
        )
    return result


def iter_ti_export_csv(rows: list[dict[str, Any]]) -> str:
    """Gera CSV UTF-8 com headers PT-BR."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(
        [
            "Nome",
            "Usuario",
            "Impressora",
            "Fila",
            "URL_IPP",
            "Padrao",
            "Departamento",
            "Local",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row["display_name"],
                row["username"],
                row["printer_display_name"],
                row["cups_queue_name"],
                row["ipp_url"] or "",
                "sim" if row["is_default"] else "nao",
                row["department"] or "",
                row["location"] or "",
            ]
        )
    return buffer.getvalue()
