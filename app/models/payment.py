from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=False)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, successful, failed

    # Relationships
    tenant = relationship("Tenant", back_populates="payments")
    contact = relationship("Contact", back_populates="payments")
    order = relationship("Order", back_populates="payments")
    events = relationship("Event", back_populates="payment", cascade="all, delete-orphan")