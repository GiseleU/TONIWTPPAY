# app/models/contact.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Contact(Base):
    """
    Represents a WhatsApp contact identity.

    Contacts are mutable and must never be required
    for Order integrity.
    """

    __tablename__ = "contacts"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)

    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ---- Relationships ----
    tenant = relationship("Tenant", back_populates="contacts")

    inquiries = relationship(
        "Inquiry",
        back_populates="contact",
        cascade="all, delete-orphan",
    )

    orders = relationship(
        "Order",
        back_populates="contact",
        cascade="all, delete-orphan",
    )

    events = relationship(
        "Event",
        back_populates="contact",
        cascade="all, delete-orphan",
    )

    consents = relationship(
        "Consent",
        back_populates="contact",
        cascade="all, delete-orphan",
    )

    opt_outs = relationship(
        "OptOut",
        back_populates="contact",
        cascade="all, delete-orphan",
    )

    compliance_signals = relationship(
        "ComplianceSignal",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
