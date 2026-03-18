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


async def handle_message(db: Session, seller_phone: str, message: str):
    """
    Handles incoming WhatsApp messages from a seller via Meta webhook.
    
    Responsibilities:
    1. Validate seller exists and is ACTIVE.
    2. Maintain workflow state for multi-product sales.
    3. Handle commands: PAY, SUMMARY.
    4. Record product, quantity, and total amount.
    5. Handle transaction finalization and summary.
    6. Return proper feedback via WhatsApp client.
    """
    # -----------------------
    # 1. Validate tenant
    # -----------------------
    tenant: Tenant | None = db.query(Tenant).filter(
        Tenant.phone_number == seller_phone,
        Tenant.coexistence_status == CoexistenceStatus.ACTIVE
    ).first()

    if not tenant:
        # Seller not onboarded or inactive
        raise HTTPException(status_code=404, detail="Seller not onboarded or inactive")

    tenant_id = tenant.id
    msg = message.strip().lower()
    state: ConversationState = get_or_create_state(db, seller_phone, tenant_id)
    client = get_whatsapp_client()

    # -----------------------
    # 2. Commands / Workflow
    # -----------------------

    # Command: Start new sale
    if msg == "pay":
        tx = create_transaction(db, seller_phone, tenant_id)
        state.state = WorkflowState.WAITING_PRODUCT.value
        state.current_transaction_id = tx.id
        db.commit()
        await client.send_message(seller_phone, "Enter product name:")
        return

    # Command: Get today's sales summary
    if msg == "summary":
        summary = build_summary(db, tenant_id)
        await client.send_message(seller_phone, summary)
        return

    # Workflow: Waiting for product name
    if state.state == WorkflowState.WAITING_PRODUCT.value:
        state.temp_product = message.strip()
        state.state = WorkflowState.WAITING_QUANTITY.value
        db.commit()
        await client.send_message(seller_phone, "Enter quantity:")
        return

    # Workflow: Waiting for quantity
    if state.state == WorkflowState.WAITING_QUANTITY.value:
        state.temp_quantity = message.strip()
        state.state = WorkflowState.WAITING_AMOUNT.value
        db.commit()
        await client.send_message(seller_phone, "Enter total amount (RWF):")
        return

    # Workflow: Waiting for total amount
    if state.state == WorkflowState.WAITING_AMOUNT.value:
        try:
            total_amount = Decimal(message.strip())
        except Exception:
            await client.send_message(
                seller_phone,
                "Invalid amount. Please enter a number for total amount (RWF)."
            )
            return

        add_item(
            db,
            transaction_id=state.current_transaction_id,
            tenant_id=tenant_id,
            product_name=state.temp_product,
            quantity=int(state.temp_quantity),
            total_amount=total_amount
        )

        state.state = WorkflowState.WAITING_ADD_MORE.value
        state.temp_product = None
        state.temp_quantity = None
        db.commit()
        buttons = [{"id": "yes", "title": "Yes"}, {"id": "no", "title": "No"}]
        await client.send_interactive_buttons(
            seller_phone, "Add another product? (yes/no)", buttons
        )
        return

    # Workflow: Waiting to add another product
    if state.state == WorkflowState.WAITING_ADD_MORE.value:
        if msg in ["yes", "y"]:
            state.state = WorkflowState.WAITING_PRODUCT.value
            db.commit()
            await client.send_message(seller_phone, "Enter product name:")
        elif msg in ["no", "n"]:
            response = finalize_transaction(db, state)
            reset_state(state, db)
            db.commit()
            await client.send_message(seller_phone, response)
        else:
            await client.send_message(seller_phone, "Please reply with 'yes' or 'no'.")
        return

    # Default fallback response
    await client.send_message(
        seller_phone,
        "Send PAY to record a sale or SUMMARY to view today's sales."
    )


# -----------------------------
# Helper Functions
# -----------------------------

def finalize_transaction(db: Session, state: ConversationState) -> str:
    """Return a summary of the current transaction."""
    items = db.query(TransactionItem).filter_by(transaction_id=state.current_transaction_id).all()
    if not items:
        return "No items recorded for this transaction."

    total = sum(i.total_amount for i in items)
    lines = ["✅ Sale recorded", "Items:"]
    for i in items:
        lines.append(f"- {i.product_name} x{i.quantity} → {i.total_amount} RWF")
    lines.append(f"\n💰 Total: {total} RWF")
    return "\n".join(lines)


def build_summary(db: Session, tenant_id: str) -> str:
    """Build a summary of all products sold today for the tenant."""
    data = generate_daily_summary(db, tenant_id, date.today())
    if not data or not data.total_orders:
        return "No sales recorded today."

    lines = ["📊 Today's Sales Summary:"]
    total = Decimal(0)
    for item in getattr(data, "items", []):
        lines.append(
            f"{item['product_name']}:\n- Qty: {item['quantity']}\n- Revenue: {item['total_amount']} RWF\n"
        )
        total += item['total_amount']
    lines.append(f"💰 Total Revenue: {total} RWF")
    return "\n".join(lines)