from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    whatsapp_accounts = relationship("WhatsAppAccount", back_populates="tenant", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="tenant", cascade="all, delete-orphan")
    inquiries = relationship("Inquiry", back_populates="tenant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="tenant", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="tenant", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="tenant", cascade="all, delete-orphan")
    consents = relationship("Consent", back_populates="tenant", cascade="all, delete-orphan")
    opt_outs = relationship("OptOut", back_populates="tenant", cascade="all, delete-orphan")