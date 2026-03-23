# app/routers/summary.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal

from app.db.session import get_db
from app.db.models_import import DailySummary
from app.services.summary_service import generate_daily_summary, get_today_summary

router = APIRouter()


# ----------------------------
# GET /summary/daily
# ----------------------------
@router.get("/summary/daily")
def get_daily_summary(
    tenant_id: str = Query(..., description="Tenant or seller ID"),
    summary_date: date = Query(default=date.today(), description="Date for summary"),
    db: Session = Depends(get_db)
):
    """
    Get the daily sales summary for a tenant/seller.
    Returns total orders, total revenue, paid orders/revenue, and per-product breakdown.
    """

    try:
        # Generate or fetch the aggregated DailySummary (totals)
        summary: DailySummary = generate_daily_summary(
            db=db,
            tenant_id=tenant_id,
            summary_date=summary_date
        )

        # Fetch real-time product-level breakdown from Transactions
        summary_items = get_today_summary(
            db=db,
            tenant_id=tenant_id,
            target_date=summary_date
        )["items"]

        # Format items for JSON response
        formatted_items = [
            {
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "total_amount": float(item["total_amount"]),
            }
            for item in summary_items
        ]

        response = {
            "tenant_id": tenant_id,
            "summary_date": summary.summary_date.isoformat(),
            "total_orders": summary.total_orders,
            "total_revenue": float(summary.total_revenue),
            "paid_orders": summary.paid_orders,
            "paid_revenue": float(summary.paid_revenue),
            "items": formatted_items,
        }

        return response

    except Exception as e:
        print(f"Error generating daily summary: {e}")
        raise HTTPException(status_code=500, detail="Could not generate summary")