# Reports API router

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.summary import DailySummaryResponse, ComplianceMetricsResponse
from app.services.summary_service import generate_daily_summary
from app.services.compliance_service import aggregate_compliance_metrics
from app.core.datetime_utils import get_today
from datetime import date
from typing import Optional

router = APIRouter()


@router.get("/reports/daily-summary", response_model=DailySummaryResponse)
def get_daily_summary(
    tenant_id: str = Query(..., description="Tenant ID"),
    summary_date: Optional[date] = Query(None, description="Date for summary, defaults to today"),
    db: Session = Depends(get_db)
):
    """
    Get or generate daily summary for a tenant on a specific date.
    """
    if not summary_date:
        summary_date = get_today()

    summary = generate_daily_summary(db, tenant_id, summary_date)
    return DailySummaryResponse.model_validate(summary)


@router.get("/reports/compliance-metrics", response_model=ComplianceMetricsResponse)
def get_compliance_metrics(
    tenant_id: str = Query(..., description="Tenant ID"),
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated compliance metrics for a tenant over a date range.
    """
    try:
        metrics = aggregate_compliance_metrics(db, tenant_id, start_date, end_date)
        return ComplianceMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aggregating metrics: {str(e)}")
