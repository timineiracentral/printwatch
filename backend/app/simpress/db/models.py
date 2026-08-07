from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.simpress.db.base import SimpressBase


class Cnpj(SimpressBase):
    __tablename__ = "cnpjs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    invoice_match_warning: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    contact_links: Mapped[list["CnpjContact"]] = relationship(
        back_populates="cnpj", cascade="all, delete-orphan"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="cnpj_ref", cascade="all, delete-orphan"
    )


class Contact(SimpressBase):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    cnpj_links: Mapped[list["CnpjContact"]] = relationship(
        back_populates="contact", cascade="all, delete-orphan"
    )


class CnpjContact(SimpressBase):
    __tablename__ = "cnpj_contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cnpj_id: Mapped[int] = mapped_column(ForeignKey("cnpjs.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    cnpj: Mapped["Cnpj"] = relationship(back_populates="contact_links")
    contact: Mapped["Contact"] = relationship(back_populates="cnpj_links")

    __table_args__ = (
        UniqueConstraint("cnpj_id", "contact_id", name="uq_cnpj_contact"),
    )


class Invoice(SimpressBase):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cnpj_id: Mapped[int] = mapped_column(ForeignKey("cnpjs.id"), nullable=False)
    contract_code: Mapped[str] = mapped_column(String(64), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    zip_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    reminder_stage: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'new'")
    )
    launch_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    cnpj_ref: Mapped["Cnpj"] = relationship(back_populates="invoices")

    __table_args__ = (
        UniqueConstraint(
            "contract_code", "invoice_number", name="uq_invoice_contract_nota"
        ),
    )


class SyncRun(SimpressBase):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    contracts_count: Mapped[int] = mapped_column(nullable=False, default=0)
    contract_codes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    invoices_upserted: Mapped[int] = mapped_column(nullable=False, default=0)
    zips_downloaded: Mapped[int] = mapped_column(nullable=False, default=0)
    cnpj_warnings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    errors_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class SendClaim(SimpressBase):
    __tablename__ = "send_claims"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    part: Mapped[str] = mapped_column(String(16), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "invoice_id", "stage", "contact_id", "part", name="uq_send_claim"
        ),
    )


class MessageAudit(SimpressBase):
    __tablename__ = "message_audit"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    part: Mapped[str] = mapped_column(String(16), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.id"), nullable=True
    )
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    outcome: Mapped[str] = mapped_column(String(8), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    variant_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
