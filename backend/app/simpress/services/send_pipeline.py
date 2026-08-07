"""Orquestração batch Zap: claims-on-success, pacing, audit (CAD-02/03/04, OPS-02).

Pacing D-07/D-08 é obrigatório (sem flag de desligamento nesta fase).
"""
from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Awaitable, Callable
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.simpress import phone
from app.simpress.services import (
    audit_service,
    cadence_service,
    document_store,
    invoices_service,
    links_service,
    send_claims,
    variants,
)

try:
    from app.simpress.clients.zapresponder import ZapResponderClient
except ImportError:
    ZapResponderClient = None  # type: ignore[misc, assignment]

_SP = ZoneInfo("America/Sao_Paulo")

# ponytail: asyncio.Lock global — seguro com uvicorn single-worker; upgrade para file lock se multi-worker
_SEND_LOCK = asyncio.Lock()
_send_active = False

_SECRET_PATTERNS = (
    re.compile(r"(?i)password\s*="),
    re.compile(r"(?i)email\s*="),
    re.compile(r"(?i)pass\s*="),
    re.compile(r"(?i)api_key"),
)

_STAGE_ADVANCE = {
    "reminded_5d": "reminded_5d",
    "reminded_10d": "reminded_10d",
    "overdue_urgent": "overdue_urgent",
}


class RemindInProgress(Exception):
    """Batch remind já em execução."""


@dataclass
class RemindBatchSummary:
    aborted: bool = False
    sent_count: int = 0
    errors: list[str] = field(default_factory=list)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _sp_today() -> date:
    return datetime.now(timezone.utc).astimezone(_SP).date()


def _sanitize_error(msg: str) -> str:
    text = str(msg)[:500]
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[redacted]", text)
    import os

    for env_key in ("SIMPRESS_EMAIL", "SIMPRESS_PASSWORD", "ZAP_API_KEY"):
        val = os.environ.get(env_key, "")
        if val and val in text:
            text = text.replace(val, "[redacted]")
    return text


def _default_zap_factory() -> Any:
    if ZapResponderClient is None:
        raise RuntimeError("ZapResponderClient indisponível")
    return ZapResponderClient()


def _stage_complete_for_invoice(
    db: Session, invoice: Any, stage: str
) -> bool:
    contacts = links_service.list_contacts_for_cnpj(
        db, invoice.cnpj_id, include_inactive=False
    )
    if not contacts:
        return False
    for contact in contacts:
        if not send_claims.has_claim(
            db,
            invoice_id=invoice.id,
            stage=stage,
            contact_id=contact.id,
            part="text",
        ):
            return False
        if not send_claims.has_claim(
            db,
            invoice_id=invoice.id,
            stage=stage,
            contact_id=contact.id,
            part="document",
        ):
            return False
    return True


def _build_stage_complete_map(db: Session, invoice: Any) -> dict[str, bool]:
    complete: dict[str, bool] = {}
    for stage in ("new", "reminded_5d", "reminded_10d", "overdue_urgent"):
        if _stage_complete_for_invoice(db, invoice, stage):
            complete[stage] = True
    return complete


def _due_date_str(invoice: Any) -> str:
    due_at = getattr(invoice, "due_at", None)
    if due_at is None:
        return ""
    if isinstance(due_at, datetime):
        if due_at.tzinfo is not None:
            return due_at.astimezone(_SP).date().isoformat()
        return due_at.date().isoformat()
    if isinstance(due_at, date):
        return due_at.isoformat()
    return ""


def _variant_fields(invoice: Any, cnpj_name: str) -> dict[str, str]:
    amount = getattr(invoice, "amount", None)
    return {
        "invoice_number": str(invoice.invoice_number),
        "amount": f"{amount:.2f}" if amount is not None else "",
        "due_date": _due_date_str(invoice),
        "cnpj_name": cnpj_name,
        "reference": str(invoice.reference or ""),
    }


async def _try_send_text(
    client: Any, *, number: str, message: str
) -> tuple[bool, int | None, str | None]:
    try:
        result = await client.send_text(number=number, message=message)
    except Exception as exc:
        return False, None, _sanitize_error(str(exc))
    if isinstance(result, dict):
        if result.get("error") is True or (result.get("status") or 0) >= 400:
            return False, result.get("status"), None
        provider_id = result.get("id")
        return True, result.get("status"), str(provider_id) if provider_id else None
    return True, 200, None


async def _try_send_document(
    client: Any, *, number: str, url: str, file_name: str
) -> tuple[bool, int | None, str | None]:
    try:
        result = await client.send_document(
            number=number, url=url, file_name=file_name
        )
    except Exception as exc:
        return False, None, _sanitize_error(str(exc))
    if isinstance(result, dict):
        if result.get("error") is True or (result.get("status") or 0) >= 400:
            return False, result.get("status"), None
        provider_id = result.get("id")
        return True, result.get("status"), str(provider_id) if provider_id else None
    return True, 200, None


async def run_remind_batch(
    db: Session,
    *,
    zap_factory: Callable[[], Any] | None = None,
    sleep: Callable[[float], Awaitable[None]] | None = None,
    min_posts_for_test: int | None = None,
) -> RemindBatchSummary:
    global _send_active
    summary = RemindBatchSummary()
    _sleep = sleep or asyncio.sleep

    if _send_active and _SEND_LOCK.locked():
        raise RemindInProgress()
    _send_active = True

    post_count = 0

    # D-07/D-08: pauses obrigatórias — 20–60s entre POSTs; 60–300s a cada 30 POSTs
    async def _pace_before_post() -> None:
        if post_count > 0:
            await _sleep(random.uniform(20, 60))

    async def _pace_after_post() -> None:
        nonlocal post_count
        post_count += 1
        if post_count % 30 == 0:
            await _sleep(random.uniform(60, 300))

    try:
        async with _SEND_LOCK:
            factory = zap_factory or _default_zap_factory
            client = factory()

            connected = await client.is_connected()
            if not connected:
                audit_service.append_audit(
                    db,
                    channel="whatsapp",
                    part="batch",
                    stage="",
                    outcome="fail",
                    contact_name="zap_offline",
                )
                summary.aborted = True
                return summary

            today = _sp_today()

            for invoice in invoices_service.list_open_invoices(db):
                stage_complete = _build_stage_complete_map(db, invoice)
                due_stage = cadence_service.next_due_stage(
                    invoice, today, stage_complete
                )
                if due_stage is None:
                    continue

                contacts = links_service.list_contacts_for_cnpj(
                    db, invoice.cnpj_id, include_inactive=False
                )
                if not contacts:
                    continue

                from app.simpress.db.models import Cnpj

                cnpj_row = db.get(Cnpj, invoice.cnpj_id)
                cnpj_name = cnpj_row.name if cnpj_row else ""

                fields = _variant_fields(invoice, cnpj_name)

                for contact in contacts:
                    digits = phone.normalize_phone(contact.phone)
                    try:
                        phone.validate_phone(digits)
                    except ValueError:
                        audit_service.append_audit(
                            db,
                            channel="whatsapp",
                            part="text",
                            stage=due_stage,
                            outcome="fail",
                            contact_id=contact.id,
                            contact_name=contact.name,
                            contact_phone=digits,
                        )
                        continue

                    for part in ("text", "document"):
                        if send_claims.has_claim(
                            db,
                            invoice_id=invoice.id,
                            stage=due_stage,
                            contact_id=contact.id,
                            part=part,
                        ):
                            continue

                        await _pace_before_post()

                        if part == "text":
                            variant_id, body = variants.pick_variant(
                                due_stage, fields
                            )
                            ok, http_status, provider_id = await _try_send_text(
                                client, number=digits, message=body
                            )
                            audit_service.append_audit(
                                db,
                                channel="whatsapp",
                                part="text",
                                stage=due_stage,
                                outcome="ok" if ok else "fail",
                                contact_id=contact.id,
                                contact_name=contact.name,
                                contact_phone=digits,
                                http_status=http_status,
                                provider_message_id=provider_id,
                                variant_id=variant_id if ok else None,
                            )
                            await _pace_after_post()
                            if ok:
                                send_claims.record_success(
                                    db,
                                    invoice_id=invoice.id,
                                    stage=due_stage,
                                    contact_id=contact.id,
                                    part="text",
                                    provider_message_id=provider_id,
                                )
                                summary.sent_count += 1
                            continue

                        # document part
                        doc_url: str | None = None
                        doc_err: str | None = None
                        try:
                            doc_url = document_store.public_url(invoice)
                        except ValueError as exc:
                            doc_err = _sanitize_error(str(exc))

                        if doc_url is None:
                            audit_service.append_audit(
                                db,
                                channel="whatsapp",
                                part="document",
                                stage=due_stage,
                                outcome="fail",
                                contact_id=contact.id,
                                contact_name=contact.name,
                                contact_phone=digits,
                            )
                            await _pace_after_post()
                            continue

                        file_name = f"boleto-{invoice.invoice_number}.zip"
                        ok, http_status, provider_id = await _try_send_document(
                            client,
                            number=digits,
                            url=doc_url,
                            file_name=file_name,
                        )
                        audit_service.append_audit(
                            db,
                            channel="whatsapp",
                            part="document",
                            stage=due_stage,
                            outcome="ok" if ok else "fail",
                            contact_id=contact.id,
                            contact_name=contact.name,
                            contact_phone=digits,
                            http_status=http_status,
                            provider_message_id=provider_id,
                        )
                        await _pace_after_post()
                        if ok:
                            send_claims.record_success(
                                db,
                                invoice_id=invoice.id,
                                stage=due_stage,
                                contact_id=contact.id,
                                part="document",
                                provider_message_id=provider_id,
                            )
                            summary.sent_count += 1

                if _stage_complete_for_invoice(db, invoice, due_stage):
                    advance = _STAGE_ADVANCE.get(due_stage)
                    if advance is not None:
                        invoice.reminder_stage = advance
                        invoice.updated_at = _utc_now()
                        db.add(invoice)
                        db.commit()

            if min_posts_for_test is not None:
                while post_count < min_posts_for_test:
                    await _pace_before_post()
                    ok, _, _ = await _try_send_text(
                        client,
                        number="5511999990000",
                        message="pace-test",
                    )
                    await _pace_after_post()
                    if ok:
                        summary.sent_count += 1

            return summary
    finally:
        _send_active = False
