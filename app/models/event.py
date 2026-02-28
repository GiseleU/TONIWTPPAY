from sqlalchemy import Column, String, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.core.enums import EventType, ActorType

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    event_type = Column(Enum(EventType), nullable=False)
    actor = Column(Enum(ActorType), nullable=False)

    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=True)
    inquiry_id = Column(String, ForeignKey("inquiries.id"), nullable=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=True)
    payment_id = Column(String, ForeignKey("payments.id"), nullable=True)

    payload = Column(JSON, nullable=False, default={})
    idempotency_key = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="events")
    contact = relationship("Contact", back_populates="events")
    inquiry = relationship("Inquiry", back_populates="events")
    order = relationship("Order", back_populates="events")
    payment = relationship("Payment", back_populates="events")