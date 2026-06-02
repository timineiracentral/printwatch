"""SNMP v2c toner + contador RFC 3805 (TONER-01/02/04, Fase 8)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable, Awaitable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Printer, PrinterMeterReading, PrinterTonerSnapshot
from app.schemas.fleet import SnmpTestResponse
from app.services import meter_service

logger = logging.getLogger(__name__)

COUNTER_TOTAL_OID = "1.3.6.1.2.1.43.10.2.1.4"
SUPPLIES_LEVEL_OID = "1.3.6.1.2.1.43.11.1.1.9"

_SNMP_GET: Callable[[str, str, str], Awaitable[int | None]] | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def resolve_community(printer: Printer) -> str:
    override = printer.snmp_community_override
    if override and override.strip():
        return override.strip()
    return settings.snmp_community


async def snmp_get_int(ip: str, community: str, oid: str) -> int | None:
    """GET SNMP integer; substituível em testes via monkeypatch."""
    global _SNMP_GET
    if _SNMP_GET is not None:
        return await _SNMP_GET(ip, community, oid)

    try:
        from pysnmp.hlapi.v3arch.asyncio import (
            CommunityData,
            ContextData,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            get_cmd,
        )
        from pysnmp.hlapi.v3arch.asyncio import ObjectIdentity
    except ImportError:
        logger.warning("pysnmp not installed")
        return None

    transport = await UdpTransportTarget.create((ip, 161), timeout=3, retries=1)
    error_indication, error_status, _error_index, var_binds = await get_cmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        transport,
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    if error_indication or error_status:
        return None
    for _oid, val in var_binds:
        try:
            return int(val)
        except (TypeError, ValueError):
            return None
    return None


async def _walk_supply_levels(ip: str, community: str) -> list[int]:
    """Walk prtMarkerSuppliesLevel — retorna valores int encontrados."""
    if _SNMP_GET is not None:
        val = await _SNMP_GET(ip, community, SUPPLIES_LEVEL_OID)
        return [val] if val is not None else []

    try:
        from pysnmp.hlapi.v3arch.asyncio import (
            CommunityData,
            ContextData,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            walk_cmd,
        )
        from pysnmp.hlapi.v3arch.asyncio import ObjectIdentity
    except ImportError:
        return []

    levels: list[int] = []
    transport = await UdpTransportTarget.create((ip, 161), timeout=3, retries=1)
    async for error_indication, error_status, _error_index, var_binds in walk_cmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        transport,
        ContextData(),
        ObjectType(ObjectIdentity(SUPPLIES_LEVEL_OID)),
        lexicographicMode=False,
    ):
        if error_indication or error_status:
            break
        for _oid, val in var_binds:
            try:
                levels.append(int(val))
            except (TypeError, ValueError):
                continue
    return levels


def _parse_toner_levels(levels: list[int]) -> tuple[int | None, int | None, bool]:
    """Heurística MVP: primeiro level = black; color = média se ≥2 markers extras."""
    if not levels:
        return None, None, False
    black_pct = max(0, min(100, levels[0]))
    if len(levels) >= 3:
        color_levels = [max(0, min(100, v)) for v in levels[1:]]
        color_pct = round(sum(color_levels) / len(color_levels))
        return black_pct, color_pct, False
    if len(levels) == 2:
        return black_pct, None, True
    return black_pct, None, False


def upsert_toner_snapshot(
    session: Session,
    printer_id: int,
    *,
    status: str,
    black_pct: int | None = None,
    color_pct: int | None = None,
    partial_color: bool = False,
) -> None:
    now = _utc_now()
    if status == "unavailable":
        black_pct = None
        color_pct = None
        partial_color = False

    row = session.get(PrinterTonerSnapshot, printer_id)
    if row is None:
        row = PrinterTonerSnapshot(
            printer_id=printer_id,
            black_pct=black_pct,
            color_pct=color_pct,
            partial_color=partial_color,
            status=status,
            checked_at=now,
        )
        session.add(row)
    else:
        row.black_pct = black_pct
        row.color_pct = color_pct
        row.partial_color = partial_color
        row.status = status
        row.checked_at = now
    session.commit()


async def poll_printer_snmp(printer: Printer, session: Session) -> None:
    if not printer.snmp_enabled or not printer.ip_address:
        return

    ip = printer.ip_address
    community = resolve_community(printer)

    try:
        counter_total = await snmp_get_int(ip, community, COUNTER_TOTAL_OID)
        levels = await _walk_supply_levels(ip, community)
        black_pct, color_pct, partial_color = _parse_toner_levels(levels)

        if not levels and counter_total is None:
            raise RuntimeError("SNMP empty response")

        upsert_toner_snapshot(
            session,
            printer.id,
            status="ok",
            black_pct=black_pct,
            color_pct=color_pct,
            partial_color=partial_color,
        )

        if counter_total is not None:
            meter_service.upsert_snmp_reading_same_day(
                session,
                printer.id,
                _utc_now(),
                counter_total,
                None,
                None,
            )
    except Exception as exc:
        logger.warning(
            "SNMP poll failed printer_id=%s ip=%s community=***REDACTED*** err=%s",
            printer.id,
            ip,
            type(exc).__name__,
        )
        upsert_toner_snapshot(session, printer.id, status="unavailable")


async def run_snmp_cycle_async(db: Session) -> int:
    printers = list(
        db.scalars(
            select(Printer).where(
                Printer.is_active.is_(True),
                Printer.snmp_enabled.is_(True),
            )
        ).all()
    )
    if not printers:
        return 0

    sem = asyncio.Semaphore(5)

    async def _one(p: Printer) -> None:
        async with sem:
            await poll_printer_snmp(p, db)

    await asyncio.gather(*[_one(p) for p in printers])
    return len(printers)


def run_snmp_cycle(db: Session) -> int:
    """Wrapper síncrono para testes e execução manual."""
    return asyncio.run(run_snmp_cycle_async(db))


async def run_snmp_test(printer_id: int, db: Session) -> SnmpTestResponse:
    printer = db.get(Printer, printer_id)
    if printer is None or not printer.is_active:
        return SnmpTestResponse(ok=False, message="Impressora não encontrada")
    if not printer.snmp_enabled:
        return SnmpTestResponse(ok=False, message="SNMP não habilitado")
    if not printer.ip_address:
        return SnmpTestResponse(ok=False, message="IP não configurado")

    ip = printer.ip_address
    community = resolve_community(printer)

    try:
        counter_total = await snmp_get_int(ip, community, COUNTER_TOTAL_OID)
        levels = await _walk_supply_levels(ip, community)
        black_pct, color_pct, partial_color = _parse_toner_levels(levels)

        if not levels and counter_total is None:
            return SnmpTestResponse(ok=False, message="Sem resposta SNMP")

        await poll_printer_snmp(printer, db)
        return SnmpTestResponse(
            ok=True,
            message="SNMP OK",
            counter_total=counter_total,
            black_pct=black_pct,
            color_pct=color_pct,
            partial_color=partial_color,
        )
    except Exception as exc:
        return SnmpTestResponse(ok=False, message=str(exc)[:200])
