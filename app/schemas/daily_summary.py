from pydantic import BaseModel, ConfigDict
from datetime import date
from decimal import Decimal
from typing import List


class ProductSummary(BaseModel):
    product_name: str
    quantity: int
    total_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


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
    products: List[ProductSummary]  # <-- Added per-product breakdown

    model_config = ConfigDict(from_attributes=True)


class ComplianceMetricsResponse(BaseModel):
    opt_outs: int
    blocked_sends: int
    failed_sends: int
    quality_warnings: int

    model_config = ConfigDict(from_attributes=True)