# app/services/summary_service.py
from sqlalchemy.orm import Session, joinedload
from datetime import date
from decimal import Decimal

from app.db.models_import import Transaction, DailySummary
from app.core.datetime_utils import get_start_of_day, get_end_of_day

# -----------------------------
# REAL-TIME SUMMARY (WhatsApp)
# -----------------------------
def get_today_summary(db: Session, tenant_id: str, target_date: date):
    """
    Real-time summary for WhatsApp.
    Uses Transaction + TransactionItem as source of truth.
    """

    start = get_start_of_day(target_date)
    end = get_end_of_day(target_date)

    transactions = (
        db.query(Transaction)
        .options(joinedload(Transaction.items))
        .filter(
            Transaction.tenant_id == tenant_id,
            Transaction.created_at >= start,
            Transaction.created_at <= end,
        )
        .all()
    )

    if not transactions:
        return {
            "total_orders": 0,
            "total_revenue": Decimal("0"),
            "gross_profit": None,
            "gross_loss": None,
            "profit_complete": False,
            "missing_cost_products": [],
            "top_revenue": None,
            "top_profit": None,
            "items": [],
        }

    product_totals: dict = {}
    total_revenue = Decimal("0")
    gross_profit = Decimal("0")
    gross_loss = Decimal("0")
    has_any_cost = False
    any_missing_cost = False

    for txn in transactions:
        for item in txn.items:
            item_total = item.total_amount or Decimal("0")
            total_revenue += item_total

            key = item.product_name
            if key not in product_totals:
                product_totals[key] = {
                    "product_name": key,
                    "quantity": 0,
                    "total_amount": Decimal("0"),
                    "total_profit": None,
                }

            product_totals[key]["quantity"] += item.quantity
            product_totals[key]["total_amount"] += item_total

            if item.profit is not None:
                p = product_totals[key]
                p["total_profit"] = (p["total_profit"] or Decimal("0")) + item.profit
                if item.profit >= 0:
                    gross_profit += item.profit
                else:
                    gross_loss += abs(item.profit)
                has_any_cost = True
            else:
                any_missing_cost = True

    items_list = list(product_totals.values())
    missing_cost_products = [p["product_name"] for p in items_list if p["total_profit"] is None]

    # Top by revenue (always available)
    top_revenue = max(items_list, key=lambda p: p["total_amount"], default=None)

    # Top by profit (only from products that have cost data and positive profit)
    profitable = [p for p in items_list if p.get("total_profit") is not None and p["total_profit"] > 0]
    top_profit = max(profitable, key=lambda p: p["total_profit"], default=None)

    return {
        "total_orders": len(transactions),
        "total_revenue": total_revenue,
        "gross_profit": gross_profit if has_any_cost else None,
        "gross_loss": gross_loss if gross_loss > 0 else None,
        "profit_complete": has_any_cost and not any_missing_cost,
        "missing_cost_products": missing_cost_products,
        "top_revenue": top_revenue,
        "top_profit": top_profit,
        "items": items_list,
    }


# -----------------------------
# BATCH SUMMARY (for background jobs)
# -----------------------------
def generate_daily_summary(
    db: Session, tenant_id: str, summary_date: date
) -> DailySummary:
    """
    Aggregated summary stored in DB (used for analytics / dashboards).
    Calculates totals from TransactionItems for robustness.
    """

    start = get_start_of_day(summary_date)
    end = get_end_of_day(summary_date)

    transactions = (
        db.query(Transaction)
        .options(joinedload(Transaction.items))
        .filter(
            Transaction.tenant_id == tenant_id,
            Transaction.created_at >= start,
            Transaction.created_at <= end,
        )
        .all()
    )

    total_orders = len(transactions)
    total_revenue = sum(
        (sum((item.total_amount or Decimal("0")) for item in txn.items) for txn in transactions),
        Decimal("0")
    )

    # Fetch existing summary or create new
    summary = (
        db.query(DailySummary)
        .filter(
            DailySummary.tenant_id == tenant_id,
            DailySummary.summary_date == summary_date,
        )
        .first()
    )

    if summary:
        summary.total_orders = total_orders
        summary.total_revenue = total_revenue
        summary.paid_orders = total_orders
        summary.paid_revenue = total_revenue
    else:
        summary = DailySummary(
            id=f"DS{tenant_id}{summary_date.strftime('%Y%m%d')}",
            tenant_id=tenant_id,
            summary_date=summary_date,
            total_orders=total_orders,
            total_revenue=total_revenue,
            paid_orders=total_orders,
            paid_revenue=total_revenue,
        )
        db.add(summary)

    db.commit()
    return summary