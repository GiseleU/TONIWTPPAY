from sqlalchemy import Column, String, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.utils import generate_uuid
from app.core.enums import EventType, ActorType


class Event(Base):
    """
    Event tracking table for all seller workflow steps.
    """

    __tablename__ = "events"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(Enum(EventType), nullable=False)
    actor = Column(Enum(ActorType), nullable=False)

    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)

    # Payload to store step-specific details: product, quantity, amount, etc.
    payload = Column(JSON, nullable=False, default={})
    idempotency_key = Column(String, unique=True, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="events")