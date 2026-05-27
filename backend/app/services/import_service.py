"""Import CSV bulk com relatório por linha (D-23–D-26)."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.normalize import normalize_org_code, normalize_printer_name
from app.db.models import CostCenter, Department, Printer, User

MAX_IMPORT_BYTES = 5 * 1024 * 1024

ENTITY_HEADERS: dict[str, tuple[str, ...]] = {
    "cost-centers": ("code", "name"),
    "departments": ("code", "name", "cost_center_code"),
    "users": (
        "cups_username",
        "display_name",
        "department_code",
        "cost_center_code",
    ),
    "printers": (
        "display_name",
        "cups_queue_name",
        "ip_address",
        "manufacturer_model",
        "location",
        "department_code",
    ),
}


@dataclass
class ImportLineError:
    line: int
    message: str


@dataclass
class ImportResult:
    total: int
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[ImportLineError] = field(default_factory=list)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _sanitize_csv_field(value: str) -> str:
    """Mitiga CSV formula injection (T-05-06a)."""
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{value}"
    return value


def _empty_to_none(value: str) -> Optional[str]:
    s = value.strip()
    return s if s else None


def _parse_csv(content: bytes, expected_headers: tuple[str, ...]) -> list[tuple[int, dict[str, str]]]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV vazio ou sem cabeçalho")

    normalized_headers = [h.strip() for h in reader.fieldnames if h is not None]
    if tuple(normalized_headers) != expected_headers:
        expected = ",".join(expected_headers)
        got = ",".join(normalized_headers)
        raise ValueError(f"cabeçalho inválido; esperado: {expected}; recebido: {got}")

    rows: list[tuple[int, dict[str, str]]] = []
    for idx, raw in enumerate(reader, start=2):
        row = {key: (raw.get(key) or "").strip() for key in expected_headers}
        rows.append((idx, row))
    return rows


def _find_cost_center_by_code(db: Session, code: str) -> Optional[CostCenter]:
    normalized = normalize_org_code(code)
    if not normalized:
        return None
    for row in db.scalars(select(CostCenter)):
        if normalize_org_code(row.code) == normalized:
            return row
    return None


def _find_department_by_code(db: Session, code: str) -> Optional[Department]:
    normalized = normalize_org_code(code)
    if not normalized:
        return None
    for row in db.scalars(select(Department)):
        if normalize_org_code(row.code) == normalized:
            return row
    return None


def _find_user_by_username(db: Session, username: str) -> Optional[User]:
    username = username.strip()
    if not username:
        return None
    return db.scalars(select(User).where(User.cups_username == username)).first()


def _find_printer_by_queue(db: Session, queue_name: str) -> Optional[Printer]:
    normalized = normalize_printer_name(queue_name)
    if not normalized:
        return None
    for row in db.scalars(select(Printer)):
        if normalize_printer_name(row.cups_queue_name) == normalized:
            return row
    return None


def _resolve_cost_center_id(
    db: Session, code: Optional[str], *, line: int
) -> tuple[Optional[int], Optional[str]]:
    if code is None:
        return None, None
    cc = _find_cost_center_by_code(db, code)
    if cc is None:
        return None, f"cost_center_code '{code}' não encontrado"
    if not cc.is_active:
        return None, f"cost_center_code '{code}' inativo"
    return cc.id, None


def _resolve_department_id(
    db: Session, code: str, *, line: int
) -> tuple[Optional[int], Optional[str]]:
    dept = _find_department_by_code(db, code)
    if dept is None:
        return None, f"department_code '{code}' não encontrado"
    if not dept.is_active:
        return None, f"department_code '{code}' inativo"
    return dept.id, None


def _apply_result(result: ImportResult, outcome: str) -> None:
    if outcome == "created":
        result.created += 1
    elif outcome == "updated":
        result.updated += 1
    elif outcome == "skipped":
        result.skipped += 1


def _upsert_cost_center(db: Session, row: dict[str, str], now: datetime) -> str:
    code = normalize_org_code(row["code"])
    if not code:
        raise ValueError("code inválido")
    name = _sanitize_csv_field(row["name"].strip())
    if not name:
        raise ValueError("name obrigatório")

    existing = _find_cost_center_by_code(db, code)
    if existing is None:
        db.add(
            CostCenter(
                code=code,
                name=name,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
        return "created"

    changed = False
    if existing.name != name:
        existing.name = name
        changed = True
    if not existing.is_active:
        existing.is_active = True
        changed = True
    if changed:
        existing.updated_at = now
        return "updated"
    return "skipped"


def _upsert_department(db: Session, row: dict[str, str], now: datetime) -> str:
    code = normalize_org_code(row["code"])
    if not code:
        raise ValueError("code inválido")
    name = _sanitize_csv_field(row["name"].strip())
    if not name:
        raise ValueError("name obrigatório")

    cc_code = _empty_to_none(row["cost_center_code"])
    cost_center_id: Optional[int] = None
    if cc_code is not None:
        cc_id, err = _resolve_cost_center_id(db, cc_code, line=0)
        if err:
            raise ValueError(err)
        cost_center_id = cc_id

    existing = _find_department_by_code(db, code)
    if existing is None:
        db.add(
            Department(
                code=code,
                name=name,
                cost_center_id=cost_center_id,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
        return "created"

    changed = False
    if existing.name != name:
        existing.name = name
        changed = True
    if existing.cost_center_id != cost_center_id:
        existing.cost_center_id = cost_center_id
        changed = True
    if not existing.is_active:
        existing.is_active = True
        changed = True
    if changed:
        existing.updated_at = now
        return "updated"
    return "skipped"


def _upsert_user(db: Session, row: dict[str, str], now: datetime) -> str:
    username = row["cups_username"].strip()
    if not username:
        raise ValueError("cups_username obrigatório")
    username = _sanitize_csv_field(username)

    display_name = _sanitize_csv_field(row["display_name"].strip())
    if not display_name:
        raise ValueError("display_name obrigatório")

    dept_code = row["department_code"].strip()
    if not dept_code:
        raise ValueError("department_code obrigatório")
    dept_id, err = _resolve_department_id(db, dept_code, line=0)
    if err:
        raise ValueError(err)

    cc_code = _empty_to_none(row["cost_center_code"])
    cost_center_id: Optional[int] = None
    if cc_code is not None:
        cc_id, cc_err = _resolve_cost_center_id(db, cc_code, line=0)
        if cc_err:
            raise ValueError(cc_err)
        cost_center_id = cc_id

    existing = _find_user_by_username(db, username)
    if existing is None:
        db.add(
            User(
                cups_username=username,
                display_name=display_name,
                department_id=dept_id,  # type: ignore[arg-type]
                cost_center_id=cost_center_id,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
        return "created"

    changed = False
    if existing.display_name != display_name:
        existing.display_name = display_name
        changed = True
    if existing.department_id != dept_id:
        existing.department_id = dept_id  # type: ignore[assignment]
        changed = True
    if existing.cost_center_id != cost_center_id:
        existing.cost_center_id = cost_center_id
        changed = True
    if not existing.is_active:
        existing.is_active = True
        changed = True
    if changed:
        existing.updated_at = now
        return "updated"
    return "skipped"


def _upsert_printer(db: Session, row: dict[str, str], now: datetime) -> str:
    display_name = _sanitize_csv_field(row["display_name"].strip())
    if not display_name:
        raise ValueError("display_name obrigatório")

    queue = normalize_printer_name(row["cups_queue_name"])
    if not queue:
        raise ValueError("cups_queue_name inválido")

    ip_address = _empty_to_none(row["ip_address"])
    if ip_address is not None:
        ip_address = _sanitize_csv_field(ip_address)
    manufacturer_model = _empty_to_none(row["manufacturer_model"])
    if manufacturer_model is not None:
        manufacturer_model = _sanitize_csv_field(manufacturer_model)
    location = _empty_to_none(row["location"])
    if location is not None:
        location = _sanitize_csv_field(location)

    dept_code = _empty_to_none(row["department_code"])
    department_id: Optional[int] = None
    if dept_code is not None:
        dept_id, err = _resolve_department_id(db, dept_code, line=0)
        if err:
            raise ValueError(err)
        department_id = dept_id

    existing = _find_printer_by_queue(db, queue)
    if existing is None:
        db.add(
            Printer(
                display_name=display_name,
                cups_queue_name=queue,
                ip_address=ip_address,
                manufacturer_model=manufacturer_model,
                location=location,
                department_id=department_id,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
        return "created"

    changed = False
    if existing.display_name != display_name:
        existing.display_name = display_name
        changed = True
    if existing.ip_address != ip_address:
        existing.ip_address = ip_address
        changed = True
    if existing.manufacturer_model != manufacturer_model:
        existing.manufacturer_model = manufacturer_model
        changed = True
    if existing.location != location:
        existing.location = location
        changed = True
    if existing.department_id != department_id:
        existing.department_id = department_id
        changed = True
    if not existing.is_active:
        existing.is_active = True
        changed = True
    if changed:
        existing.updated_at = now
        return "updated"
    return "skipped"


_UPSERT_HANDLERS: dict[str, Callable[[Session, dict[str, str], datetime], str]] = {
    "cost-centers": _upsert_cost_center,
    "departments": _upsert_department,
    "users": _upsert_user,
    "printers": _upsert_printer,
}


def import_csv(
    db: Session,
    entity: str,
    content: bytes,
    *,
    strict: bool = False,
) -> ImportResult:
    if entity not in ENTITY_HEADERS:
        raise ValueError(f"entity inválida: {entity}")

    headers = ENTITY_HEADERS[entity]
    handler = _UPSERT_HANDLERS[entity]

    try:
        parsed_rows = _parse_csv(content, headers)
    except ValueError as exc:
        return ImportResult(total=0, errors=[ImportLineError(line=1, message=str(exc))])

    result = ImportResult(total=len(parsed_rows))
    now = _utc_now()

    if strict:
        outcomes: list[str | ImportLineError] = []
        for line_num, row in parsed_rows:
            try:
                outcomes.append(handler(db, row, now))
            except ValueError as exc:
                outcomes.append(ImportLineError(line=line_num, message=str(exc)))

        result.errors = [o for o in outcomes if isinstance(o, ImportLineError)]
        if result.errors:
            db.rollback()
            return result

        for outcome in outcomes:
            assert isinstance(outcome, str)
            _apply_result(result, outcome)
        db.commit()
        return result

    for line_num, row in parsed_rows:
        try:
            outcome = handler(db, row, now)
            db.commit()
            _apply_result(result, outcome)
        except ValueError as exc:
            db.rollback()
            result.errors.append(ImportLineError(line=line_num, message=str(exc)))
        except Exception:
            db.rollback()
            raise

    return result
