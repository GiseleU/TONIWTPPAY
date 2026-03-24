from sqlalchemy import Column, String, Date, DateTime, Numeric, Integer, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from decimal import Decimal
from app.db.utils import generate_uuid


class DailySummary(Base):
    """
    Aggregated daily summary for tenant performance and compliance monitoring.

    Profit fields follow the same convention as Transaction:
    - total_profit: NULL means no cost data at all, 0 means cost == revenue
    - profit_complete: True only if every item that day had cost_per_unit
    """

    __tablename__ = "daily_summaries"

    # ---- Identity ----
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)

    # ---- Date ----
    summary_date = Column(Date, nullable=False)

    # ---- Revenue & Orders ----
    total_orders = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Numeric(12, 2), nullable=False, default=Decimal(0))
    paid_orders = Column(Integer, nullable=False, default=0)
    paid_revenue = Column(Numeric(12, 2), nullable=False, default=Decimal(0))

    # ---- Profit Tracking ----
    total_profit = Column(Numeric(12, 2), nullable=True)
    profit_complete = Column(Boolean, nullable=False, default=False)

    # ---- Compliance Metrics ----
    opt_outs = Column(Integer, nullable=False, default=0)
    blocked_sends = Column(Integer, nullable=False, default=0)
    failed_sends = Column(Integer, nullable=False, default=0)
    quality_warnings = Column(Integer, nullable=False, default=0)

    # ---- Timestamps ----
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ---- Relationships ----
    tenant = relationship("Tenant", back_populates="daily_summaries")