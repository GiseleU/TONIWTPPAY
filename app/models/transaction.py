from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from decimal import Decimal
from app.db.base import Base
from app.db.utils import generate_uuid


class Transaction(Base):
    """
    Transaction representing a sale by a seller (multi-product).

    Profit fields:
    - total_profit: sum of profit only for items where cost_per_unit is known.
                    NULL means no items had cost_per_unit (profit fully unknown).
                    0 means cost == revenue for tracked items.
    - profit_complete: True only if every item in this transaction has cost_per_unit.
    - items_missing_cost_count: how many items are missing cost_per_unit.
                                Powers partial profit nudge in WhatsApp flow.
    """

    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    seller_phone = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    total_amount = Column(Numeric(12, 2), default=Decimal('0'), nullable=False)

    # --- Profit tracking ---
    total_profit = Column(Numeric(12, 2), nullable=True)
    profit_complete = Column(Boolean, nullable=False, default=False)
    items_missing_cost_count = Column(Integer, nullable=False, default=0)

    # ---- Relationships ----
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")
    tenant = relationship("Tenant", back_populates="transactions")