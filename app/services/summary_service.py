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
            "items": [],
        }

    product_totals = {}
    total_revenue = Decimal("0")
    total_profit: Decimal | None = None

    for txn in transactions:
        for item in txn.items:
            item_total = item.total_amount or Decimal("0")
            total_revenue += item_total

            if item.product_name not in product_totals:
                product_totals[item.product_name] = {
                    "product_name": item.product_name,
                    "quantity": 0,
                    "total_amount": Decimal("0"),
                    "total_profit": None,
                }

            product_totals[item.product_name]["quantity"] += item.quantity
            product_totals[item.product_name]["total_amount"] += item_total

            if item.profit is not None:
                p = product_totals[item.product_name]
                p["total_profit"] = (p["total_profit"] or Decimal("0")) + item.profit
                total_profit = (total_profit or Decimal("0")) + item.profit

    return {
        "total_orders": len(transactions),
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "items": list(product_totals.values()),
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