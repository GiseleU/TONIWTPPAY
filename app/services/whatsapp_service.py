# app/services/whatsapp_service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import date

from app.models.tenant import Tenant
from app.models.transaction_item import TransactionItem
from app.models.conversation_state import ConversationState

from app.services.state_service import get_or_create_state, reset_state
from app.services.transaction_service import create_transaction, add_item
from app.services.summary_service import generate_daily_summary

from app.core.enums import WorkflowState, CoexistenceStatus
from app.integrations.whatsapp_client import get_whatsapp_client


async def handle_message(
    db: Session,
    seller_phone: str,
    message: str,
):
    """
    Handles incoming WhatsApp messages via Meta webhook.
    Flow: phone_number → Tenant → Workflow
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
    msg = (message or "").strip().lower()
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
            "Enter <product> <quantity> <unit price> / Andika <igicuruzwa> <ingano> <igiciro>\n"
            "Ex: amagi 2 600"
        )
        return

    if msg == "summary":
        summary = build_summary(db, tenant_id)
        await client.send_message(seller_phone, summary)
        return

    # -----------------------
    # 3. Workflow states
    # -----------------------
    # ---- Product line input ----
    if state.state == WorkflowState.WAITING_PRODUCT_LINE.value:
        parts = message.strip().split()
        if len(parts) != 3:
            await client.send_message(
                seller_phone,
                "Invalid format. Please enter: <product> <quantity> <unit price>.\n"
                "Ex: amagi 2 600"
            )
            return

        product_name, quantity_str, unit_price_str = parts
        try:
            quantity = int(quantity_str)
            unit_price = Decimal(unit_price_str)
        except Exception:
            await client.send_message(
                seller_phone,
                "Quantity must be an integer and unit price must be a number.\nEx: amagi 2 600"
            )
            return

        total_amount = quantity * unit_price
        add_item(
            db,
            transaction_id=state.current_transaction_id,
            tenant_id=tenant_id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=total_amount
        )

        state.state = WorkflowState.WAITING_ADD_MORE.value
        db.commit()

        buttons = [{"id": "yes", "title": "Yes"}, {"id": "no", "title": "No"}]
        await client.send_interactive_buttons(
            seller_phone,
            f"Added {product_name} x{quantity} @ {unit_price} RWF each → {total_amount} RWF\n"
            "Add another product?",
            buttons
        )
        return

    # ---- Add more products ----
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
            # Use the new finalize_transaction function
            response = finalize_transaction(db, state)
            reset_state(state, db)
            db.commit()
            await client.send_message(seller_phone, response)
            return

        else:
            await client.send_message(
                seller_phone,
                "Please reply with 'yes' or 'no'."
            )
            return

    # -----------------------
    # 4. Default fallback
    # -----------------------
    await client.send_message(
        seller_phone,
        "Send PAY to record a sale or SUMMARY to view today's sales."
    )


# -----------------------------
# HELPER: finalize transaction
# -----------------------------
def finalize_transaction(db: Session, state: ConversationState) -> str:
    items = db.query(TransactionItem).filter_by(
        transaction_id=state.current_transaction_id
    ).all()

    if not items:
        return "No items recorded for this transaction."

    total = sum(i.total_amount for i in items)
    lines = ["✅ Sale recorded", "Items:"]
    for i in items:
        lines.append(f"- {i.product_name} x{i.quantity} @ {i.unit_price} → {i.total_amount} RWF")
    lines.append(f"\n💰 Total: {total} RWF")
    
    # Reset state after finalizing transaction
    reset_state(state, db)
    db.commit()
    
    return "\n".join(lines)


# -----------------------------
# HELPER: build summary
# -----------------------------
def build_summary(db: Session, tenant_id: str) -> str:
    data = generate_daily_summary(db, tenant_id, date.today())
    if not data or not data.total_orders:
        return "No sales recorded today."

    lines = ["📊 Today's Sales Summary:"]
    total = Decimal(0)
    for item in getattr(data, "items", []):
        lines.append(
            f"{item['product_name']}:\n"
            f"- Qty: {item['quantity']}\n"
            f"- Revenue: {item['total_amount']} RWF\n"
        )
        total += item['total_amount']

    lines.append(f"💰 Total Revenue: {total} RWF")
    return "\n".join(lines)