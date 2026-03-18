# app/routers/summary.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from app.db.session import get_db
from app.services.summary_service import generate_daily_summary

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
    Returns total orders, total revenue, and per-product breakdown.
    """
    try:
        summary = generate_daily_summary(db=db, tenant_id=tenant_id, summary_date=summary_date)

        # Format response
        response = {
            "tenant_id": tenant_id,
            "summary_date": summary.summary_date,
            "total_orders": summary.total_orders,
            "total_revenue": float(summary.total_revenue),
            "paid_orders": summary.paid_orders,
            "paid_revenue": float(summary.paid_revenue),
            # Optionally include product breakdown if DailySummary has items attribute
            "items": getattr(summary, "items", [])
        }

        return response

    except Exception as e:
        print(f"Error generating daily summary: {e}")
        raise HTTPException(status_code=500, detail="Could not generate summary")