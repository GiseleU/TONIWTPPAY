# app/models/opt_out.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.models.contact import Contact
from app.models.tenant import Tenant  # import Tenant for relationship

class OptOut(Base):
    """
    Represents an opt-out preference for a contact.
    """

    __tablename__ = "opt_outs"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)  # <-- added
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=True)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ---- Relationships ----
    tenant = relationship("Tenant", back_populates="opt_outs")
    contact = relationship("Contact", back_populates="opt_outs")