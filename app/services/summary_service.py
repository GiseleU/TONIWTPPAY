# app/services/summary_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from decimal import Decimal
from app.db.models_import import Transaction, TransactionItem, DailySummary


def generate_daily_summary(db: Session, tenant_id: str, summary_date: date) -> DailySummary:
    """
    Generate daily summary for a tenant:
      - total orders
      - total revenue
      - product-level breakdown
    """

    # 1. Query all transactions for the tenant on the given date
    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.tenant_id == tenant_id,
            func.date(Transaction.created_at) == summary_date,
        )
        .all()
    )

    total_orders = len(transactions)

    # 2. Aggregate total revenue and product-level breakdown
    product_totals = {}
    total_revenue = Decimal(0)

    for txn in transactions:
        # Explicitly iterate over TransactionItems
        items: list[TransactionItem] = txn.items
        for item in items:
            total_revenue += item.total_amount

            if item.product_name not in product_totals:
                product_totals[item.product_name] = {
                    "product_name": item.product_name,
                    "quantity": 0,
                    "total_amount": Decimal(0),
                }

            product_totals[item.product_name]["quantity"] += item.quantity
            product_totals[item.product_name]["total_amount"] += item.total_amount

    products_list = list(product_totals.values())

    # 3. Check if a DailySummary already exists
    summary = (
        db.query(DailySummary)
        .filter(
            DailySummary.tenant_id == tenant_id,
            DailySummary.summary_date == summary_date,
        )
        .first()
    )

    if summary:
        # Update existing summary
        summary.total_orders = total_orders
        summary.total_revenue = total_revenue
        summary.paid_orders = total_orders
        summary.paid_revenue = total_revenue
    else:
        # Create new summary
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