"""Cálculo de custo no read path e CRUD de tarifas globais (D-01..D-04, D-11..D-14)."""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, Literal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import CostCenter, CostRate, Department, PrintJob, User
from app.schemas.cost_rates import CostRateCreate
from app.services.policy_service import compute_outside_policy, load_policy_context

_TZ = ZoneInfo(settings.api_timezone)
_UTC = timezone.utc

BUCKET_UNASSIGNED_CC = "Não atribuído"
BUCKET_UNREGISTERED_USER = "Usuário não cadastrado"
BUCKET_UNREGISTERED_PRINTER = "Impressora não cadastrada"
BUCKET_PENDING_PAGES = "Páginas pendentes"

_BUCKET_KEYS = frozenset(
    {
        "_unassigned_cc",
        "_unregistered_user",
        "_unregistered_printer",
        "_pending_pages",
    }
)


def _utc_now() -> datetime:
    return datetime.now(_UTC).replace(tzinfo=None)


def _local_date_to_utc_range(d: date) -> tuple[datetime, datetime]:
    start_local = datetime.combine(d, time(0, 0, 0), tzinfo=_TZ)
    end_local = datetime.combine(d, time(23, 59, 59, 999_999), tzinfo=_TZ)
    return start_local.astimezone(_UTC), end_local.astimezone(_UTC)


def format_money_brl(value: Decimal | None) -> str | None:
    """Formata Decimal como R$ com 2 casas (exibição)."""
    if value is None:
        return None
    quantized = value.quantize(Decimal("0.01"))
    return f"R$ {quantized:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def rate_at(db: Session, at: datetime) -> CostRate | None:
    """Tarifa vigente em `at`: maior valid_from <= at (D-02)."""
    ts = at
    if ts.tzinfo is not None:
        ts = ts.astimezone(_UTC).replace(tzinfo=None)
    return db.scalars(
        select(CostRate)
        .where(CostRate.valid_from <= ts)
        .order_by(CostRate.valid_from.desc())
        .limit(1)
    ).first()


def line_cost(rate: CostRate | None, color_mode: str | None) -> Decimal | None:
    """Custo de uma linha (1 página). None se sem tarifa ou color_mode inválido."""
    if rate is None or color_mode is None:
        return None
    if color_mode == "mono":
        return Decimal(rate.rate_mono)
    if color_mode == "color":
        return Decimal(rate.rate_color)
    return None


def _new_bucket_row(group_key: str, group_label: str) -> dict[str, Any]:
    return {
        "group_key": group_key,
        "group_label": group_label,
        "pages_mono": 0,
        "pages_color": 0,
        "pages_pending": 0,
        "estimated_cost": Decimal("0"),
        "is_bucket": True,
    }


def _ensure_bucket(buckets: dict[str, dict[str, Any]], key: str, label: str) -> dict[str, Any]:
    if key not in buckets:
        buckets[key] = _new_bucket_row(key, label)
    return buckets[key]


def _load_org_maps(
    db: Session,
) -> tuple[dict[str, User], dict[int, Department], dict[int, CostCenter]]:
    users = {
        u.cups_username.lower(): u
        for u in db.scalars(select(User).where(User.is_active.is_(True))).all()
    }
    departments = {
        d.id: d for d in db.scalars(select(Department).where(Department.is_active.is_(True))).all()
    }
    cost_centers = {
        cc.id: cc
        for cc in db.scalars(select(CostCenter).where(CostCenter.is_active.is_(True))).all()
    }
    return users, departments, cost_centers


def _effective_cost_center_id(
    user: User, departments: dict[int, Department]
) -> int | None:
    if user.cost_center_id is not None:
        return user.cost_center_id
    dept = departments.get(user.department_id)
    if dept is not None:
        return dept.cost_center_id
    return None


def aggregate_cost_by_dimension(
    db: Session,
    date_from: date,
    date_to: date,
    dimension: Literal["cost_center", "department"],
) -> list[dict[str, Any]]:
    """Agrega páginas faturáveis e custo por CC ou departamento (COST-04).

    Exclui outside_policy (D-14). Linhas printer_id NULL vão só ao bucket
    Impressora não cadastrada (D-13). color_mode NULL → bucket Páginas pendentes.
    """
    start_utc, _ = _local_date_to_utc_range(date_from)
    _, end_utc = _local_date_to_utc_range(date_to)

    policy_ctx = load_policy_context(db)
    users, departments, cost_centers = _load_org_maps(db)

    groups: dict[str, dict[str, Any]] = {}
    buckets: dict[str, dict[str, Any]] = {}

    stmt = (
        select(PrintJob)
        .where(PrintJob.timestamp >= start_utc)
        .where(PrintJob.timestamp <= end_utc)
        .order_by(PrintJob.timestamp.asc())
    )

    for job in db.scalars(stmt):
        if compute_outside_policy(policy_ctx, job.username, job.printer_id):
            continue

        rate = rate_at(db, job.timestamp)
        cost = line_cost(rate, job.color_mode) or Decimal("0")

        if job.color_mode is None:
            row = _ensure_bucket(buckets, "_pending_pages", BUCKET_PENDING_PAGES)
            row["pages_pending"] += 1
            continue

        if job.color_mode == "mono":
            mono_inc, color_inc = 1, 0
        elif job.color_mode == "color":
            mono_inc, color_inc = 0, 1
        else:
            continue

        if job.printer_id is None:
            row = _ensure_bucket(
                buckets, "_unregistered_printer", BUCKET_UNREGISTERED_PRINTER
            )
            row["pages_mono"] += mono_inc
            row["pages_color"] += color_inc
            row["estimated_cost"] += cost
            continue

        user = users.get(job.username.lower())
        if user is None:
            row = _ensure_bucket(
                buckets, "_unregistered_user", BUCKET_UNREGISTERED_USER
            )
            row["pages_mono"] += mono_inc
            row["pages_color"] += color_inc
            row["estimated_cost"] += cost
            continue

        if dimension == "cost_center":
            cc_id = _effective_cost_center_id(user, departments)
            if cc_id is None:
                group_key = "_unassigned_cc"
                group_label = BUCKET_UNASSIGNED_CC
                target = buckets
            else:
                cc = cost_centers.get(cc_id)
                code = cc.code if cc else str(cc_id)
                name = cc.name if cc else ""
                group_key = f"cc:{cc_id}"
                group_label = f"{code} — {name}" if name else code
                target = groups
        else:
            dept = departments.get(user.department_id)
            if dept is None:
                group_key = "_unregistered_user"
                group_label = BUCKET_UNREGISTERED_USER
                target = buckets
            else:
                group_key = f"dept:{dept.id}"
                group_label = f"{dept.code} — {dept.name}"
                target = groups

        if group_key not in target:
            target[group_key] = {
                "group_key": group_key,
                "group_label": group_label,
                "pages_mono": 0,
                "pages_color": 0,
                "pages_pending": 0,
                "estimated_cost": Decimal("0"),
                "is_bucket": group_key in _BUCKET_KEYS,
            }
        row = target[group_key]
        row["pages_mono"] += mono_inc
        row["pages_color"] += color_inc
        row["estimated_cost"] += cost

    result: list[dict[str, Any]] = sorted(
        groups.values(),
        key=lambda r: r["group_label"].lower(),
    )

    for key in (
        "_unassigned_cc",
        "_unregistered_user",
        "_unregistered_printer",
        "_pending_pages",
    ):
        if key in buckets:
            result.append(buckets[key])

    return result


# --- Tarifas (CRUD) ---


def list_cost_rates(db: Session) -> list[CostRate]:
    return list(
        db.scalars(select(CostRate).order_by(CostRate.valid_from.desc())).all()
    )


def get_current_cost_rate(db: Session) -> CostRate | None:
    return rate_at(db, _utc_now())


def create_cost_rate(db: Session, payload: CostRateCreate) -> CostRate:
    now = _utc_now()
    valid_from = payload.valid_from if payload.valid_from is not None else now
    if valid_from.tzinfo is not None:
        valid_from = valid_from.astimezone(_UTC).replace(tzinfo=None)

    row = CostRate(
        rate_mono=payload.rate_mono,
        rate_color=payload.rate_color,
        valid_from=valid_from,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
