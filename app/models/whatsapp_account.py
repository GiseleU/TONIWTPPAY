from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class WhatsAppAccount(Base):
    __tablename__ = "whatsapp_accounts"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="whatsapp_accounts")
    inquiries = relationship("Inquiry", back_populates="whatsapp_account", cascade="all, delete-orphan")