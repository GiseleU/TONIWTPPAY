# app/models/order_line_item.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from decimal import Decimal


class OrderLineItem(Base):
    """
    Represents a line item in an order.
    
    Tracks individual products in an order with quantity and pricing.
    """

    __tablename__ = "order_line_items"

    # ---- Identity ----
    id = Column(String, primary_key=True)  # LI####
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)

    # ---- Product Details ----
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

    # ---- Timestamps ----
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ---- Relationships ----
    order = relationship("Order", back_populates="line_items")

    @property
    def subtotal(self) -> Decimal:
        """Calculate subtotal (quantity * unit_price)."""
        return self.quantity * Decimal(str(self.unit_price))
