# Analytics/summary response schemas

from pydantic import BaseModel, ConfigDict
from datetime import date
from decimal import Decimal
from typing import Dict


class DailySummaryResponse(BaseModel):
    id: str
    tenant_id: str
    summary_date: date
    total_orders: int
    total_revenue: Decimal
    paid_orders: int
    paid_revenue: Decimal
    total_inquiries: int
    confirmed_inquiries: int
    dropped_inquiries: int
    opt_outs: int
    blocked_sends: int
    failed_sends: int
    quality_warnings: int

    model_config = ConfigDict(from_attributes=True)


class ComplianceMetricsResponse(BaseModel):
    opt_outs: int
    blocked_sends: int
    failed_sends: int
    quality_warnings: int

    model_config = ConfigDict(from_attributes=True)
