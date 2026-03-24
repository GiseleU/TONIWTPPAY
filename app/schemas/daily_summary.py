from pydantic import BaseModel, ConfigDict
from datetime import date
from decimal import Decimal
from typing import List, Optional


class ProductSummary(BaseModel):
    product_name: str
    quantity: int
    total_amount: Decimal
    total_profit: Optional[Decimal] = None      # None if no cost data for this product
    margin: Optional[Decimal] = None            # None if no cost data for this product
    has_profit: bool = False                    # True if at least one item had cost_per_unit

    model_config = ConfigDict(from_attributes=True)


class DailySummaryResponse(BaseModel):
    id: str
    tenant_id: str
    summary_date: date
    total_orders: int
    total_revenue: Decimal
    paid_orders: int
    paid_revenue: Decimal
    total_profit: Optional[Decimal] = None      # None = no cost data at all
    profit_complete: bool = False               # True only if all items had cost_per_unit
    margin: Optional[Decimal] = None            # None if no cost data at all
    opt_outs: int
    blocked_sends: int
    failed_sends: int
    quality_warnings: int
    products: List[ProductSummary]

    model_config = ConfigDict(from_attributes=True)


class ComplianceMetricsResponse(BaseModel):
    opt_outs: int
    blocked_sends: int
    failed_sends: int
    quality_warnings: int

    model_config = ConfigDict(from_attributes=True)