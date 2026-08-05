"""Orquestração single-flight portal → faturas → ZIP (SYNC-01..04)."""
from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.simpress.db.models import SyncRun
from app.simpress.cnpj_id import normalize_cnpj
from app.simpress.services import cnpjs_service, document_store, invoices_service

try:
    from app.simpress.clients.simpress_portal import SimpressPortalClient
except ImportError:
    SimpressPortalClient = None  # type: ignore[misc, assignment]

# ponytail: asyncio.Lock global — seguro com uvicorn single-worker; upgrade para file lock se multi-worker
_SYNC_LOCK = asyncio.Lock()
_sync_active = False

_SECRET_PATTERNS = (
    re.compile(r"(?i)password\s*="),
    re.compile(r"(?i)email\s*="),
    re.compile(r"(?i)pass\s*="),
    re.compile(r"(?i)api_key"),
)


class SyncInProgress(Exception):
    """Sync manual/cron já em execução (D-01)."""


def _default_portal_factory() -> Any:
    if SimpressPortalClient is None:
        raise RuntimeError("SimpressPortalClient indisponível")
    return SimpressPortalClient()


def is_sync_running() -> bool:
    return _sync_active


def reserve_sync() -> None:
    global _sync_active
    if _sync_active:
        raise SyncInProgress()
    _sync_active = True


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _sanitize_error(msg: str) -> str:
    text = str(msg)[:500]
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[redacted]", text)
    for env_key in ("SIMPRESS_EMAIL", "SIMPRESS_PASSWORD", "ZAP_API_KEY"):
        import os

        val = os.environ.get(env_key, "")
        if val and val in text:
            text = text.replace(val, "[redacted]")
    return text


def _dump_list(items: list[Any], *, limit: int | None = None) -> str:
    data = items[:limit] if limit is not None else items
    return json.dumps(data, ensure_ascii=False)


def get_last_sync_summary(db: Session) -> SyncRun | None:
    return db.scalars(select(SyncRun).order_by(SyncRun.started_at.desc())).first()


async def run_sync(
    db: Session,
    *,
    portal_factory: Callable[[], Any] | type | None = None,
) -> SyncRun:
    global _sync_active
    if _sync_active and _SYNC_LOCK.locked():
        raise SyncInProgress()
    if not _sync_active:
        _sync_active = True

    try:
        async with _SYNC_LOCK:
            run = SyncRun(started_at=_utc_now(), ok=False)
            db.add(run)
            db.commit()
            db.refresh(run)

            errors: list[str] = []
            warnings: list[str] = []
            invoices_upserted = 0
            zips_downloaded = 0
            ok = True
            portal: Any | None = None

            try:
                active_cnpjs = cnpjs_service.list_cnpjs(db, include_inactive=False)
                if not active_cnpjs:
                    # ponytail: sem CNPJs cadastrados não abre portal — evita listagem “contrato inteiro”
                    run.contracts_count = 0
                    run.contract_codes_json = _dump_list([])
                else:
                    factory = portal_factory or _default_portal_factory
                    portal = factory() if callable(factory) else factory()
                    if hasattr(portal, "open"):
                        await portal.open()

                    page_size = getattr(portal, "page_size", 25)

                    contracts = await portal.fetch_contracts()
                    contract_codes = sorted(
                        {
                            str(c.get("codigoContrato"))
                            for c in contracts
                            if c.get("codigoContrato")
                        }
                    )
                    run.contracts_count = len(contract_codes)
                    run.contract_codes_json = _dump_list(contract_codes)

                    for cnpj_row in active_cnpjs:
                        matched_any = False
                        total_for_cnpj = 0
                        page = 1
                        while True:
                            rows, total = await portal.list_invoices(
                                contract_codes=contract_codes,
                                cnpj=cnpj_row.cnpj,
                                page=page,
                                page_size=page_size,
                            )
                            total_for_cnpj = total
                            for row in rows:
                                row_cnpj = normalize_cnpj(str(row.get("cnpj") or ""))
                                if row_cnpj != cnpj_row.cnpj:
                                    continue
                                status = invoices_service._normalize_status(
                                    row.get("statusPagamento")
                                )
                                if status is None:
                                    continue
                                matched_any = True
                                if status in invoices_service.OPEN_STATUSES:
                                    inv = invoices_service.upsert_open_invoice(
                                        db, cnpj_row.id, cnpj_row.cnpj, row
                                    )
                                    invoices_upserted += 1
                                    if inv.zip_token is None:
                                        contract_code, invoice_number = (
                                            invoices_service._portal_keys(row)
                                        )
                                        raw = await portal.download_zip(
                                            contract_code=contract_code,
                                            invoice_number=invoice_number,
                                        )
                                        document_store.save_zip(db, inv, raw)
                                        zips_downloaded += 1
                                elif status in invoices_service.CLOSED_STATUSES:
                                    invoices_service.mark_closed_and_purge_zip(
                                        db, row, status
                                    )
                            if page * page_size >= total:
                                break
                            page += 1

                        if total_for_cnpj == 0:
                            cnpj_row.invoice_match_warning = True
                            warnings.append(cnpj_row.cnpj)
                            db.add(cnpj_row)
                            db.commit()
                        elif matched_any and cnpj_row.invoice_match_warning:
                            cnpj_row.invoice_match_warning = False
                            db.add(cnpj_row)
                            db.commit()
                            warnings = [w for w in warnings if w != cnpj_row.cnpj]
            except SyncInProgress:
                raise
            except Exception as exc:
                ok = False
                errors.append(_sanitize_error(str(exc)))
            finally:
                if portal is not None:
                    try:
                        await portal.close()
                    except Exception as exc:
                        ok = False
                        errors.append(_sanitize_error(str(exc)))

                run.finished_at = _utc_now()
                run.ok = ok and not errors
                run.invoices_upserted = invoices_upserted
                run.zips_downloaded = zips_downloaded
                run.cnpj_warnings_json = _dump_list(sorted(set(warnings)))
                run.errors_json = _dump_list(errors[:5], limit=5)
                db.add(run)
                db.commit()
                db.refresh(run)

            return run
    finally:
        _sync_active = False


def clear_manual_sync_task() -> None:
    global _sync_active
    _sync_active = False
