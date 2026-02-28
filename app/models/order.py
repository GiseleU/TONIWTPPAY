from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from decimal import Decimal


class Order(Base):
    """
    Represents a confirmed, immutable customer order.

    Created only after:
    - inquiry confirmation
    - customer details capture
    """

    __tablename__ = "orders"

    # ---- Identity ----
    id = Column(String, primary_key=True)  # O####
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=True)

    inquiry_id = Column(
        String,
        ForeignKey("inquiries.id"),
        nullable=False,
        unique=True,  # Enforce 1 inquiry → 1 order
    )

    # ---- Commercial Snapshot ----
    amount = Column(Numeric(10, 2), nullable=False)

    # ---- Customer Snapshot (Data Minimization) ----
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    customer_address = Column(String, nullable=True)

    # ---- Status ----
    status = Column(String, nullable=False, default="pending")  # pending | completed | paid

    # ---- Compliance ----
    retention_tag = Column(String, nullable=False, default="order_core")

    # ---- Timestamps ----
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ---- Relationships ----
    tenant = relationship("Tenant", back_populates="orders")
    contact = relationship("Contact", back_populates="orders")
    inquiry = relationship("Inquiry", back_populates="order")

    payments = relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    events = relationship(
        "Event",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    @property
    def total_paid(self) -> Decimal:
        """Compute total paid from all payments."""
        return sum(payment.amount for payment in self.payments) if self.payments else Decimal(0)

    def is_fully_paid(self) -> bool:
        """Check if order is fully paid."""
        return self.total_paid >= self.amount
