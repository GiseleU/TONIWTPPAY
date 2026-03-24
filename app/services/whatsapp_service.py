# app/services/whatsapp_service.py

import logging
from datetime import datetime
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
    seller_name = tenant.name.split()[0]  # first name only
    msg = message.strip().lower()
    state: ConversationState = get_or_create_state(db, seller_phone, tenant_id)
    client = get_whatsapp_client()

    # -----------------------
    # 2. Commands
    # -----------------------
    if msg == "pay":
        tx = transaction_service.create_transaction(db, seller_phone, tenant_id)
        state.state = WorkflowState.WAITING_PRODUCT_LINE.value
        state.current_transaction_id = tx.id
        db.commit()

        await client.send_message(
            seller_phone,
            "🛍️ New sale! What did you sell?\n\nEnter: <product> <quantity> <unit price>\nEx: amashu 3 3000"
        )
        return

    if msg == "summary":
        summary_msg = build_summary(db, tenant_id, seller_name)
        await client.send_message(seller_phone, summary_msg)
        return

    # -----------------------
    # 3. Workflow states
    # -----------------------

    # ---- Product line input ----
    if state.state == WorkflowState.WAITING_PRODUCT_LINE.value:
        parts = message.strip().split()

        if len(parts) < 3:
            await client.send_message(
                seller_phone,
                "Invalid format.\nUse: <product> <quantity> <unit price>\nEx: amashu 3 3000"
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
                "Quantity must be a whole number and price must be a number.\nEx: amashu 3 3000"
            )
            return

        # Save to temp fields, move to WAITING_COST
        state.temp_product_name = product_name
        state.temp_quantity = quantity_str
        state.temp_unit_price = unit_price_str
        state.state = WorkflowState.WAITING_COST.value
        db.commit()

        await client.send_message(
            seller_phone,
            f"Nice! And what did each *{product_name}* cost you? (or type *skip*)"
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
            item = transaction_service.add_item(
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
            await client.send_message(seller_phone, "❌ Error recording item. Try PAY again.")
            return

        # Clear temp fields, advance state
        state.temp_product_name = None
        state.temp_quantity = None
        state.temp_unit_price = None
        state.state = WorkflowState.WAITING_ADD_MORE.value
        db.commit()

        # Per-item confirmation with profit if cost was provided
        if item.profit is not None:
            cost_total = (cost_per_unit * quantity).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            confirmation = (
                f"✅ Sold *{product_name}* x{quantity} → {_fmt(item.total_amount)} RWF\n"
                f"💸 Cost: {_fmt(cost_total)} RWF\n"
                f"🟢 Profit: *{_fmt(item.profit)} RWF* on this sale 💪\n\n"
                f"Add another product?"
            )
        else:
            confirmation = (
                f"✅ Added *{product_name}* x{quantity} → {_fmt(item.total_amount)} RWF\n\n"
                f"Add another product?"
            )

        await client.send_interactive_buttons(
            seller_phone,
            confirmation,
            [{"id": "yes", "title": "Yes"}, {"id": "no", "title": "No"}]
        )
        return

    # ---- Add more ----
    if state.state == WorkflowState.WAITING_ADD_MORE.value:
        if msg in ("yes", "y"):
            state.state = WorkflowState.WAITING_PRODUCT_LINE.value
            db.commit()
            await client.send_message(
                seller_phone,
                "Enter: <product> <quantity> <unit price>\nEx: amashu 3 3000"
            )
            return

        elif msg in ("no", "n"):
            transaction_id = state.current_transaction_id
            sale_msg = _build_sale_summary(db, transaction_id, tenant_id, seller_name)
            reset_state(state, db)
            await client.send_message(seller_phone, sale_msg)
            return

        else:
            await client.send_interactive_buttons(
                seller_phone,
                "Add another product?",
                [{"id": "yes", "title": "Yes"}, {"id": "no", "title": "No"}]
            )
            return

    # -----------------------
    # 4. Default fallback
    # -----------------------
    if state.state == WorkflowState.IDLE.value:
        await client.send_message(
            seller_phone,
            "Send *PAY* to record a sale or *SUMMARY* to view today's sales."
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


def _build_sale_summary(
    db: Session,
    transaction_id: str,
    tenant_id: str,
    seller_name: str,
) -> str:
    """Build the gamified sale confirmation after finalization."""
    result = transaction_service.finalize_transaction(db, transaction_id, tenant_id)

    # Today's running totals (includes this transaction)
    today = get_today_summary(db, tenant_id, get_today())

    lines = ["🎉 Sale locked in!\n"]
    for item in result.items:
        if item.profit is not None:
            lines.append(
                f"📦 {item.product_name} x{item.quantity} → {_fmt(item.total_amount)} RWF"
                f" | Profit: {_fmt(item.profit)} RWF"
            )
        else:
            lines.append(
                f"📦 {item.product_name} x{item.quantity} → {_fmt(item.total_amount)} RWF"
            )

    lines.append(f"\n💰 Total today so far: *{_fmt(today['total_revenue'])} RWF*")

    today_profit = today.get("total_profit")
    today_profit_complete = today.get("profit_complete", False)

    if today_profit is not None:
        if today_profit_complete:
            lines.append(f"🟢 Profit: *{_fmt(today_profit)} RWF*")
        else:
            tracked = [i["product_name"] for i in today["items"] if i.get("total_profit") is not None]
            product_str = ", ".join(f"*{n}*" for n in tracked)
            lines.append(f"🟢 Profit from {product_str}: *{_fmt(today_profit)} RWF*")

    # Nudge for items in this transaction missing cost
    missing_in_tx = [i.product_name for i in result.items if i.cost_per_unit is None]
    if missing_in_tx and result.total_profit is not None:
        names = ", ".join(f"*{n}*" for n in missing_in_tx)
        lines.append(f"💡 Add cost for {names} next time to see your full profit")
    elif result.total_profit is None:
        lines.append("💡 Try adding costs next time to start tracking profit!")

    lines.append(f"\nYou're doing great today, {seller_name}! 🔥")

    return "\n".join(lines)


def build_summary(db: Session, tenant_id: str, seller_name: str) -> str:
    """Build the gamified daily summary."""
    data = get_today_summary(db, tenant_id, get_today())

    if not data["total_orders"]:
        return (
            f"No sales recorded today yet, {seller_name}. "
            f"Send *PAY* to record your first sale! 💪"
        )

    day_name = datetime.now().strftime("%A")

    lines = [f"🌟 *{seller_name}'s Report — {day_name}*\n"]
    lines.append("📦 *What you sold:*")

    best_product = None
    best_revenue = Decimal("0")
    thin_margin_products: list[tuple[str, int]] = []

    for item in data["items"]:
        product_name = item["product_name"]
        qty = item["quantity"]
        total = item["total_amount"]
        profit = item.get("total_profit")

        if total > best_revenue:
            best_revenue = total
            best_product = product_name

        if profit is not None:
            margin = (
                (profit / total * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                if total else Decimal("0")
            )
            lines.append(
                f"• {product_name} x{qty} → {_fmt(total)} RWF | 🟢 Profit: {_fmt(profit)} RWF"
            )
            if margin < 20:
                thin_margin_products.append((product_name, int(margin)))
        else:
            lines.append(f"• {product_name} x{qty} → {_fmt(total)} RWF")

    lines.append(f"\n💰 Revenue: *{_fmt(data['total_revenue'])} RWF*")

    total_profit = data.get("total_profit")
    profit_complete = data.get("profit_complete", False)
    if total_profit is not None and data["total_revenue"] > 0:
        if profit_complete:
            margin_pct = (total_profit / data["total_revenue"] * 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
            lines.append(f"🟢 Profit: *{_fmt(total_profit)} RWF*")
            lines.append(f"📈 Margin: *{margin_pct}%*")
        else:
            tracked = [item["product_name"] for item in data["items"] if item.get("total_profit") is not None]
            product_str = ", ".join(f"*{n}*" for n in tracked)
            lines.append(f"🟢 Profit from {product_str}: *{_fmt(total_profit)} RWF*")

    if best_product:
        lines.append(f"\n🏆 Best seller today: *{best_product}*")

    if thin_margin_products:
        name, margin = thin_margin_products[0]
        lines.append(f"💡 {name} has a thin margin ({margin}%) — worth reviewing your price?")

    # Nudge for products without cost data
    no_cost_products = [item["product_name"] for item in data["items"] if item.get("total_profit") is None]
    if no_cost_products and total_profit is not None:
        # Some products have cost, some don't — partial profit shown
        names = ", ".join(f"*{n}*" for n in no_cost_products[:2])
        suffix = "..." if len(no_cost_products) > 2 else ""
        lines.append(f"💡 Profit shown is partial — add cost for {names}{suffix} to see the full picture")
    elif no_cost_products and total_profit is None:
        lines.append("💡 Add costs when recording sales to start tracking your daily profit")

    sales_count = data["total_orders"]
    lines.append(
        f"\n{sales_count} sale{'s' if sales_count != 1 else ''} recorded today. Keep it up! 🚀"
    )

    return "\n".join(lines)
