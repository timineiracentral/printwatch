"""Agenda diária de sync Simpress às 08:00 America/Sao_Paulo (D-02)."""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.simpress.config import simpress_settings
from app.simpress.db.session import SimpressSessionLocal
from app.simpress.services import send_pipeline, sync_service

logger = logging.getLogger(__name__)
_TZ = ZoneInfo(simpress_settings.timezone)


def should_run_daily(now: datetime, last_run_date: date | None) -> bool:
    local = now.astimezone(_TZ) if now.tzinfo else now.replace(tzinfo=_TZ)
    if local.hour < simpress_settings.sync_hour:
        return False
    today = local.date()
    if last_run_date is not None and last_run_date >= today:
        return False
    return True


def _last_local_run_date(db) -> date | None:
    summary = sync_service.get_last_sync_summary(db)
    if summary is None or summary.finished_at is None:
        return None
    finished = summary.finished_at
    if finished.tzinfo is None:
        finished = finished.replace(tzinfo=_TZ)
    return finished.astimezone(_TZ).date()


async def daily_sync_loop() -> None:
    while True:
        try:
            now = datetime.now(_TZ)
            db = SimpressSessionLocal()
            try:
                last = _last_local_run_date(db)
                if should_run_daily(now, last) and not sync_service.is_sync_running():
                    try:
                        await sync_service.run_sync(db)
                    except sync_service.SyncInProgress:
                        pass
                    except Exception:
                        logger.exception("daily sync falhou")
                    try:
                        await send_pipeline.run_remind_batch(db)
                    except send_pipeline.RemindInProgress:
                        pass
                    except Exception:
                        logger.exception("daily remind batch falhou")
            finally:
                db.close()
        except Exception:
            logger.exception("daily sync loop erro")
        await asyncio.sleep(60)
