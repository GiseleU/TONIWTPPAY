# app/services/whatsapp_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.tenant import Tenant
from app.models.transaction_item import TransactionItem
from app.models.conversation_state import ConversationState

from app.services.state_service import get_or_create_state, reset_state
from app.services.transaction_service import create_transaction, add_item
from app.services.summary_service import get_today_summary

import logging
from sqlalchemy.exc import SQLAlchemyError

from app.core.enums import WorkflowState, CoexistenceStatus
from app.core.datetime_utils import get_today
from app.integrations.whatsapp_client import get_whatsapp_client


async def handle_message(
    db: Session,
    seller_phone: str,
    message: str,
):
    """
    Handles incoming WhatsApp messages via Meta webhook.
    """

    # -----------------------
    # 1. Resolve tenant
    # -----------------------
    tenant = db.query(Tenant).filter(
        Tenant.phone_number == seller_phone,
        Tenant.coexistence_status == CoexistenceStatus.ACTIVE
    ).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not active")

    tenant_id = tenant.id

    # Ignore empty messages
    if not message or not message.strip():
        return 
    
    msg = message.strip().lower()
    state: ConversationState = get_or_create_state(db, seller_phone, tenant_id)
    client = get_whatsapp_client()

    # -----------------------
    # 2. Commands
    # -----------------------
    if msg == "pay":
        tx = create_transaction(db, seller_phone, tenant_id)
        state.state = WorkflowState.WAITING_PRODUCT_LINE.value
        state.current_transaction_id = tx.id
        db.commit()

        await client.send_message(
            seller_phone,
            "Enter <product> <quantity> <unit price>\nEx: amagi 2 600"
        )
        return

    if msg == "summary":
        summary = build_summary(db, tenant_id)
        await client.send_message(seller_phone, summary)
        return

    # -----------------------
    # 3. Workflow states
    # -----------------------

    # ---- Product input ----
    if state.state == WorkflowState.WAITING_PRODUCT_LINE.value:
        parts = message.strip().split()

        if len(parts) < 3:
            await client.send_message(
                seller_phone,
                "Invalid format.\nUse: <product> <quantity> <unit price>\nEx: amagi 2 600"
            )
            return

        # Multi-word product support
        product_name = " ".join(parts[:-2])
        quantity_str = parts[-2]
        unit_price_str = parts[-1]

        try:
            quantity = int(quantity_str)
            unit_price = Decimal(unit_price_str)
        except Exception:
            await client.send_message(
                seller_phone,
                "Quantity must be integer and price must be number.\nEx: amagi 2 600"
            )
            return

        try:
            logger = logging.getLogger(__name__)
            logger.info(
                f"Adding item: tx={state.current_transaction_id}, "
                f"{product_name} x{quantity}@{unit_price}"
            )

            add_item(
                db,
                transaction_id=state.current_transaction_id,
                tenant_id=tenant_id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price
            )

            state.state = WorkflowState.WAITING_ADD_MORE.value
            db.commit()

            await client.send_interactive_buttons(
                seller_phone,
                f"✅ Added {product_name} x{quantity} → {quantity * unit_price} RWF\n"
                "Add another product?",
                [{"id": "yes", "title": "Yes"}, {"id": "no", "title": "No"}]
            )
            return

        except ValueError:
            await client.send_message(
                seller_phone,
                "❌ Transaction error. Try PAY again."
            )
            return

        except SQLAlchemyError:
            await client.send_message(
                seller_phone,
                "❌ Database error. Try again."
            )
            return

        except Exception:
            await client.send_message(
                seller_phone,
                "❌ Unexpected error. Try PAY again."
            )
            return

    # ---- Add more ----
    if state.state == WorkflowState.WAITING_ADD_MORE.value:
        if msg in ["yes", "y"]:
            state.state = WorkflowState.WAITING_PRODUCT_LINE.value
            db.commit()

            await client.send_message(
                seller_phone,
                "Enter <product> <quantity> <unit price>\nEx: amagi 2 600"
            )
            return

        elif msg in ["no", "n"]:
            response = finalize_transaction(db, state)
            reset_state(state,db)
            await client.send_message(seller_phone, response)
            return

        else:
            await client.send_message(
                seller_phone,
                "Reply 'yes' or 'no'."
            )
            return

    # --------------------------------------
    # 4. Default fallback for unknown commands
    # ---------------------------------------
    if state.state in [WorkflowState.IDLE.value]:
        # Seller sent something other than PAY or SUMMARY
        await client.send_message(
            seller_phone,
            "Send PAY to record a sale or SUMMARY to view today's sales."
        )
        return 


# -----------------------------
# FINALIZE TRANSACTION
# -----------------------------
def finalize_transaction(db: Session, state: ConversationState) -> str:
    items = db.query(TransactionItem).filter_by(
        transaction_id=state.current_transaction_id
    ).all()

    if not items:
        return "No items recorded."

    total = sum((i.total_amount for i in items), Decimal("0"))

    lines = ["✅ Sale recorded", "Items:"]

    for i in items:
        lines.append(
            f"- {i.product_name} x{i.quantity} @ {i.unit_price} → {i.total_amount} RWF"
        )

    lines.append(f"\n💰 Total: {total} RWF")

    # Reset AFTER building response
    reset_state(state, db)
    db.commit()

    return "\n".join(lines)


# -----------------------------
# BUILD SUMMARY
# -----------------------------
def build_summary(db: Session, tenant_id: str) -> str:
    data = get_today_summary(db, tenant_id, get_today())

    if not data["total_orders"]:
        return "No sales recorded today."

    lines = [
        "📊 Today's Sales Summary:",
        "",
        "Items:"
    ]

    for item in data["items"]:
        lines.append(
            f"- {item['product_name']} x{item['quantity']} → {item['total_amount']} RWF"
        )

    lines.append("")
    lines.append(f"💰 Total Revenue: {data['total_revenue']} RWF")

    return "\n".join(lines)