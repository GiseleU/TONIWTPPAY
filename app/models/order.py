from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=False)
    inquiry_id = Column(String, ForeignKey("inquiries.id"), nullable=False, unique=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String, nullable=False, default="pending")  # e.g., pending, paid, completed

    # Relationships
    tenant = relationship("Tenant", back_populates="orders")
    contact = relationship("Contact", back_populates="orders")
    inquiry = relationship("Inquiry", back_populates="order")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="order", cascade="all, delete-orphan")
