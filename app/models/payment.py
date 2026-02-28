from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    verified_by = Column(String, nullable=False)  # Actor who verified the payment
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    method = Column(String, nullable=False)  # e.g., 'cash', 'bank', 'momo'
    notes = Column(Text, nullable=True)  # Optional audit notes

    # Relationships
    tenant = relationship("Tenant", back_populates="payments")
    order = relationship("Order", back_populates="payments")
    events = relationship("Event", back_populates="payment", cascade="all, delete-orphan")
