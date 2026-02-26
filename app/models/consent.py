# app/models/consent.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.models.contact import Contact
from app.models.tenant import Tenant  # import Tenant for relationship

class Consent(Base):
    """
    Represents a consent given by a contact.
    """

    __tablename__ = "consents"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)  # <-- added
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=True)
    consented = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ---- Relationships ----
    tenant = relationship("Tenant", back_populates="consents")
    contact = relationship("Contact", back_populates="consents")