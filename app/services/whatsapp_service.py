# app/services/whatsapp_service.py

import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.datetime_utils import get_today
from app.core.enums import CoexistenceStatus, WorkflowState
from app.integrations.whatsapp_client import get_whatsapp_client
from app.models.conversation_state import ConversationState
from app.models.tenant import Tenant
from app.services import transaction_service
from app.services.state_service import get_or_create_state, reset_state
from app.services.summary_service import get_today_summary

logger = logging.getLogger(__name__)


async def handle_message(db: Session, seller_phone: str, message: str):
    """
    Handles incoming WhatsApp messages via Meta webhook.
    """

    # -----------------------
    # 1. Resolve tenant
    # -----------------------
    tenant = db.query(Tenant).filter(
        Tenant.phone_number == seller_phone,
        Tenant.coexistence_status == CoexistenceStatus.ACTIVE,
    ).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not active")

    if not message or not message.strip():
        return

    tenant_id = tenant.id
    msg = message.strip().lower()
    state: ConversationState = get_or_create_state(db, seller_phone, tenant_id)
    client = get_whatsapp_client()

    # Track last message time for Meta 24h messaging window
    state.last_message_at = datetime.now(timezone.utc)
    db.commit()

    # -----------------------
    # 2. SET COST — works from any state
    # -----------------------
    upper = message.strip().upper()
    if upper.startswith("SET ") and " COST " in upper:
        cost_idx = upper.find(" COST ")
        product_name = message.strip()[4:cost_idx].strip()
        cost_str = message.strip()[cost_idx + 6:].strip()

        if not product_name:
            await client.send_message(
                seller_phone,
                "Format: SET product COST price\nEx: SET amagi COST 200"
            )
            return

        try:
            cost_per_unit = Decimal(cost_str)
        except Exception:
            await client.send_message(
                seller_phone,
                "Cost must be a number.\nEx: SET amagi COST 200"
            )
            return

        result = transaction_service.set_product_cost(
            db, tenant_id, product_name, cost_per_unit, get_today()
        )

        if result is None:
            await client.send_message(
                seller_phone,
                f"❌ No sales of *{product_name}* found today."
            )
            return

        profit = result["product_profit"]
        profit_line = (
            f"🟢 Profit ({result['product_name']}): {_fmt(profit)} RWF"
            if profit >= 0
            else f"🔴 Loss ({result['product_name']}): {_fmt(abs(profit))} RWF"
        )
        lines = [f"✅ Cost saved for {result['product_name']}", profit_line]

        today = get_today_summary(db, tenant_id, get_today())
        missing = today.get("missing_cost_products", [])

        if missing:
            lines.append(f"\n⚠️ {len(missing)} products still missing cost: {', '.join(missing)}")
            lines.append(f"Add cost to fully track profit. Send:\nSET product COST cost_per_unit")
            lines.append(f"Ex: SET {missing[0]} COST 200")
        else:
            lines.append("\n" + _format_summary_block(today, include_details_hint=False))

        await client.send_message(seller_phone, "\n".join(lines))
        return

    # -----------------------
    # 3. Global commands
    # -----------------------
    if msg == "sale":
        if state.state not in (WorkflowState.IDLE.value, WorkflowState.COMPLETED.value):
            await client.send_message(
                seller_phone,
                "⚠️ Sale recording in progress.\nSend next product or type DONE"
            )
            return

        tx = transaction_service.create_transaction(db, seller_phone, tenant_id)
        state.state = WorkflowState.WAITING_PRODUCT_LINE.value
        state.current_transaction_id = tx.id
        db.commit()

        await client.send_message(
            seller_phone,
            "🛍️ New sale\n\nEnter: product quantity price\nEx: amagi 2 600"
        )
        return

    if msg == "summary":
        today = get_today_summary(db, tenant_id, get_today())
        await client.send_message(seller_phone, build_summary(today))
        return

    if msg == "details":
        today = get_today_summary(db, tenant_id, get_today())
        await client.send_message(seller_phone, build_details(today))
        return

    # -----------------------
    # 4. Workflow states
    # -----------------------

    # ---- Product line input ----
    if state.state == WorkflowState.WAITING_PRODUCT_LINE.value:
        if msg == "done":
            if not state.current_transaction_id:
                await client.send_message(seller_phone, "No active sale found. Send SALE to start.")
                return

            sale_msg = _build_sale_summary(db, state.current_transaction_id, tenant_id)
            reset_state(state, db)
            await client.send_message(seller_phone, sale_msg)
            return

        parts = message.strip().split()
        if len(parts) < 3:
            await client.send_message(
                seller_phone,
                "Invalid format.\nEnter: product quantity price\nEx: amagi 2 600"
            )
            return

        product_name = " ".join(parts[:-2])
        quantity_str = parts[-2]
        unit_price_str = parts[-1]

        try:
            quantity = int(quantity_str)
            Decimal(unit_price_str)  # validate only
        except Exception:
            await client.send_message(
                seller_phone,
                "Quantity must be a whole number and price must be a number.\nEx: amagi 2 600"
            )
            return

        state.temp_product_name = product_name
        state.temp_quantity = quantity_str
        state.temp_unit_price = unit_price_str
        state.state = WorkflowState.WAITING_COST.value
        db.commit()

        await client.send_message(
            seller_phone,
            f"Cost per {product_name}? (type number or skip)"
        )
        return

    # ---- Cost input ----
    if state.state == WorkflowState.WAITING_COST.value:
        product_name = state.temp_product_name
        quantity = int(state.temp_quantity)
        unit_price = Decimal(state.temp_unit_price)

        cost_per_unit: Decimal | None = None
        if msg not in ("skip", "s", "0"):
            try:
                cost_per_unit = Decimal(message.strip())
            except Exception:
                await client.send_message(
                    seller_phone,
                    "Enter a number for the cost, or type *skip*."
                )
                return

        try:
            transaction_service.add_item(
                db,
                transaction_id=state.current_transaction_id,
                tenant_id=tenant_id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                cost_per_unit=cost_per_unit,
            )
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f"Error adding item: {e}")
            await client.send_message(seller_phone, "❌ Error recording item. Try SALE again.")
            return

        state.temp_product_name = None
        state.temp_quantity = None
        state.temp_unit_price = None
        state.state = WorkflowState.WAITING_PRODUCT_LINE.value
        db.commit()

        await client.send_message(
            seller_phone,
            f"✅ {product_name} x{quantity} recorded\nSend next product or type DONE"
        )
        return

    # -----------------------
    # 5. Default fallback
    # -----------------------
    if state.state == WorkflowState.IDLE.value:
        await client.send_message(
            seller_phone,
            "Send SALE to record a sale, SUMMARY for today's totals, or DETAILS for per product breakdown."
        )
        return


# ----------------------------------------
# HELPERS
# ----------------------------------------

def _fmt(value: Decimal) -> str:
    """Format a Decimal as a clean integer if whole, else 2 decimal places."""
    if value == value.to_integral_value():
        return f"{int(value):,}"
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _missing_cost_nudge(missing: list[str]) -> str:
    names = ", ".join(missing)
    return (
        f"⚠️ {len(missing)} product{'s' if len(missing) != 1 else ''} missing cost: {names}\n"
        f"Add cost to fully track profit. Send:\n"
        f"SET product COST cost_per_unit\n"
        f"Ex: SET {missing[0]} COST 200"
    )


def _format_summary_block(today: dict, include_details_hint: bool = True) -> str:
    """
    Core summary block shared between DONE confirmation and SUMMARY command.
    """
    if not today["total_orders"]:
        return "No sales recorded today. Send SALE to start."

    lines = ["📊 Today so far:"]
    lines.append(f"💰 Revenue: {_fmt(today['total_revenue'])} RWF")

    gross_profit = today.get("gross_profit")
    gross_loss = today.get("gross_loss")
    profit_complete = today.get("profit_complete", False)
    missing = today.get("missing_cost_products", [])
    top_revenue = today.get("top_revenue")
    top_profit = today.get("top_profit")

    if gross_profit is not None:
        lines.append(f"🟢 Profit: {_fmt(gross_profit)} RWF")
    if gross_loss is not None:
        lines.append(f"🔴 Loss: {_fmt(gross_loss)} RWF")

    if top_revenue:
        lines.append(f"🏆 Top revenue: {top_revenue['product_name']} — {_fmt(top_revenue['total_amount'])} RWF")

    if top_profit:
        incomplete_flag = " ⚠️ incomplete" if not profit_complete else ""
        lines.append(f"🏆 Top profit: {top_profit['product_name']} — {_fmt(top_profit['total_profit'])} RWF{incomplete_flag}")

    if missing:
        lines.append("\n" + _missing_cost_nudge(missing))

    if include_details_hint:
        lines.append("\nSend DETAILS for per product breakdown")

    return "\n".join(lines)


def _build_sale_summary(db: Session, transaction_id: str, tenant_id: str) -> str:
    """Build sale confirmation shown after DONE."""
    transaction_service.finalize_transaction(db, transaction_id, tenant_id)
    today = get_today_summary(db, tenant_id, get_today())

    missing = today.get("missing_cost_products", [])
    profit_complete = today.get("profit_complete", False)

    lines = ["✅ Sale saved"]
    lines.append("📊 Today so far:")
    lines.append(f"💰 Revenue: {_fmt(today['total_revenue'])} RWF")

    gross_profit = today.get("gross_profit")
    gross_loss = today.get("gross_loss")

    if gross_profit is not None:
        lines.append(f"🟢 Profit: {_fmt(gross_profit)} RWF")
    if gross_loss is not None:
        lines.append(f"🔴 Loss: {_fmt(gross_loss)} RWF")

    # Show top products only when all costs are known
    if profit_complete:
        top_revenue = today.get("top_revenue")
        top_profit = today.get("top_profit")
        if top_revenue:
            lines.append(f"🏆 Top revenue: {top_revenue['product_name']} — {_fmt(top_revenue['total_amount'])} RWF")
        if top_profit:
            lines.append(f"🏆 Top profit: {top_profit['product_name']} — {_fmt(top_profit['total_profit'])} RWF")

    if missing:
        lines.append("\n" + _missing_cost_nudge(missing))

    return "\n".join(lines)


def build_summary(today: dict) -> str:
    """SUMMARY command — always shows top products, flags incomplete profit."""
    if not today["total_orders"]:
        return "No sales recorded today. Send SALE to start."
    return _format_summary_block(today, include_details_hint=True)


def build_details(today: dict) -> str:
    """DETAILS command — per product breakdown."""
    if not today["total_orders"]:
        return "No sales recorded today."

    lines = ["📊 Today — per product:"]
    for item in today["items"]:
        name = item["product_name"]
        qty = item["quantity"]
        revenue = item["total_amount"]
        profit = item.get("total_profit")

        if profit is None:
            lines.append(f"- {name} x{qty}: Revenue {_fmt(revenue)} RWF | ⚠️ No cost")
        elif profit >= 0:
            lines.append(f"- {name} x{qty}: Revenue {_fmt(revenue)} RWF | 🟢 Profit {_fmt(profit)} RWF")
        else:
            lines.append(f"- {name} x{qty}: Revenue {_fmt(revenue)} RWF | 🔴 Loss {_fmt(abs(profit))} RWF")

    missing = today.get("missing_cost_products", [])
    if missing:
        lines.append("\n" + _missing_cost_nudge(missing))

    return "\n".join(lines)
