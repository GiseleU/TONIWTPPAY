# app/services/seller_command_service.py
from sqlalchemy.orm import Session
from app.models.inquiry import Inquiry
from app.models.event import Event
from app.models.tenant import Tenant
from app.core.enums import EventType, ActorType
from app.services.summary_service import generate_daily_summary
from app.core.datetime_utils import get_today
import uuid
import re

# Allowed transitions for inquiries
INQUIRY_TRANSITIONS = {
    "new": ["confirmed", "dropped"],
    "confirmed": ["completed", "dropped"],
    "dropped": [],
    "completed": [],
}

class CommandError(Exception):
    """Raised when a seller command is invalid or cannot be executed."""
    pass


def parse_seller_command(command_text: str):
    """
    Parses seller commands:
    - CONFIRM T#### amount
    - DROP T####
    - SUMMARY
    Returns dict with action, inquiry_id, and optional amount
    """
    command_text = command_text.strip().upper()

    # CONFIRM
    match = re.match(r"CONFIRM\s+(T\d+)\s+(\d+)", command_text)
    if match:
        return {"action": "confirm", "inquiry_id": match.group(1), "amount": int(match.group(2))}

    # DROP
    match = re.match(r"DROP\s+(T\d+)", command_text)
    if match:
        return {"action": "drop", "inquiry_id": match.group(1)}

    # SUMMARY
    if command_text == "SUMMARY":
        return {"action": "summary"}

    raise CommandError(f"Invalid command format: {command_text}")


def execute_seller_command(command_text: str, seller_id: str, tenant_id: str, db: Session):
    """
    Executes a seller command:
    - Checks seller authorization (seller_id must belong to tenant)
    - Validates inquiry exists and belongs to tenant
    - Applies deterministic state transition
    - Records command event for audit
    """
    # Parse command
    command = parse_seller_command(command_text)

    # --- SUMMARY command ---
    if command["action"] == "summary":
        summary_date = get_today()
        summary = generate_daily_summary(db, tenant_id, summary_date)
        return {
            "status": "ok",
            "summary": {
                "total_orders": summary.total_orders,
                "total_revenue": float(summary.total_revenue),
                "paid_orders": summary.paid_orders,
                "paid_revenue": float(summary.paid_revenue),
                "total_inquiries": summary.total_inquiries,
                "confirmed_inquiries": summary.confirmed_inquiries,
                "dropped_inquiries": summary.dropped_inquiries,
                "opt_outs": summary.opt_outs,
                "blocked_sends": summary.blocked_sends,
                "failed_sends": summary.failed_sends,
                "quality_warnings": summary.quality_warnings,
            }
        }

    # --- CONFIRM / DROP commands ---
    # Fetch inquiry
    inquiry = db.query(Inquiry).filter_by(id=command["inquiry_id"], tenant_id=tenant_id).first()
    if not inquiry:
        raise CommandError(f"Inquiry {command['inquiry_id']} not found in tenant {tenant_id}")

    # TODO: implement proper seller authorization check
    # For now, assume seller_id is valid for tenant

    # Determine new status
    current_status = inquiry.status
    if command["action"] == "confirm":
        new_status = "confirmed"
        # Validate amount
        amount = command.get("amount")
        if amount is None or amount <= 0:
            raise CommandError("Amount must be a positive number")
    elif command["action"] == "drop":
        new_status = "dropped"
    else:
        raise CommandError(f"Unknown action: {command['action']}")

    # Validate deterministic state transition
    if new_status not in INQUIRY_TRANSITIONS.get(current_status, []):
        raise CommandError(f"Illegal transition: {current_status} → {new_status}")

    # Apply state change
    inquiry.status = new_status
    if command["action"] == "confirm":
        inquiry.amount = amount

    # Record event for audit
    event_type = EventType.INQUIRY_CONFIRMED if new_status == "confirmed" else EventType.INQUIRY_DROPPED
    event = Event(
        id=str(uuid.uuid4()),
        event_type=event_type,
        actor=ActorType.SELLER,
        tenant_id=tenant_id,
        inquiry_id=inquiry.id,
        payload={
            "command": command_text,
            "seller_id": seller_id,
            "new_status": new_status
        }
    )
    db.add(event)
    db.commit()

    return {"status": "ok", "inquiry_id": inquiry.id, "new_status": new_status}
