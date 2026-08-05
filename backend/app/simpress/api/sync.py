"""API manual sync + diagnóstico (SYNC-04)."""
from __future__ import annotations

import asyncio
import json
import threading

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.simpress.db.session import SimpressSessionLocal, get_simpress_db
from app.simpress.schemas.sync import SyncStatusRead, SyncSummaryRead
from app.simpress.services import sync_service

router = APIRouter()


def _parse_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [str(x) for x in data] if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _to_summary(run) -> SyncSummaryRead:
    return SyncSummaryRead(
        started_at=run.started_at,
        finished_at=run.finished_at,
        ok=run.ok,
        contracts_count=run.contracts_count or 0,
        contract_codes=_parse_json_list(run.contract_codes_json),
        invoices_upserted=run.invoices_upserted or 0,
        zips_downloaded=run.zips_downloaded or 0,
        cnpj_warnings=_parse_json_list(run.cnpj_warnings_json),
        errors=_parse_json_list(run.errors_json),
    )


async def _run_sync_background() -> None:
    db = SimpressSessionLocal()
    try:
        await sync_service.run_sync(db)
    except sync_service.SyncInProgress:
        pass
    except Exception:
        pass
    finally:
        db.close()


def _run_sync_thread() -> None:
    try:
        asyncio.run(_run_sync_background())
    finally:
        sync_service.clear_manual_sync_task()


@router.post("", status_code=202)
async def trigger_sync() -> dict:
    try:
        sync_service.reserve_sync()
    except sync_service.SyncInProgress:
        raise HTTPException(status_code=409, detail="sync em andamento")
    threading.Thread(target=_run_sync_thread, daemon=True).start()
    return {"status": "accepted"}


@router.get("/status", response_model=SyncStatusRead)
def sync_status() -> SyncStatusRead:
    return SyncStatusRead(in_progress=sync_service.is_sync_running())


@router.get("/last", response_model=SyncSummaryRead)
def last_sync(db: Session = Depends(get_simpress_db)) -> SyncSummaryRead:
    run = sync_service.get_last_sync_summary(db)
    if run is None:
        raise HTTPException(status_code=404, detail="nenhum sync executado")
    return _to_summary(run)
