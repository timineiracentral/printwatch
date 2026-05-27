"""Testes outside_policy (05.2-03)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Department, PrintJob, Printer, User, UserPrinterAccess
from app.services.policy_service import PolicyContext, compute_outside_policy


def _seed_user_printer(db: Session) -> tuple[User, Printer]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    dept = Department(
        code="TI",
        name="TI",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(dept)
    db.flush()
    user = User(
        cups_username="DOMAIN\\alice",
        display_name="Alice",
        department_id=dept.id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    printer = Printer(
        display_name="Lab",
        cups_queue_name="lab",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add_all([user, printer])
    db.flush()
    return user, printer


def test_unknown_user_false(db_session: Session) -> None:
    ctx = PolicyContext()
    assert compute_outside_policy(ctx, "nobody", 1) is False


def test_printer_id_none_false(db_session: Session) -> None:
    user, _ = _seed_user_printer(db_session)
    ctx = PolicyContext(username_to_user_id={"domain\\alice": user.id})
    assert compute_outside_policy(ctx, "DOMAIN\\alice", None) is False


def test_user_no_assignments_false(db_session: Session) -> None:
    user, printer = _seed_user_printer(db_session)
    ctx = PolicyContext(username_to_user_id={"domain\\alice": user.id})
    assert compute_outside_policy(ctx, "DOMAIN\\alice", printer.id) is False


def test_printer_outside_policy_true(db_session: Session) -> None:
    user, printer = _seed_user_printer(db_session)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    other = Printer(
        display_name="Other",
        cups_queue_name="other",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(other)
    db_session.flush()
    db_session.add(
        UserPrinterAccess(
            user_id=user.id,
            printer_id=printer.id,
            is_active=True,
            is_default=True,
            created_at=now,
            updated_at=now,
        )
    )
    db_session.commit()
    ctx = PolicyContext(
        username_to_user_id={"domain\\alice": user.id},
        user_allowed_printers={user.id: {printer.id}},
    )
    assert compute_outside_policy(ctx, "DOMAIN\\alice", other.id) is True


def test_printer_inside_policy_false(db_session: Session) -> None:
    user, printer = _seed_user_printer(db_session)
    ctx = PolicyContext(
        username_to_user_id={"domain\\alice": user.id},
        user_allowed_printers={user.id: {printer.id}},
    )
    assert compute_outside_policy(ctx, "DOMAIN\\alice", printer.id) is False
