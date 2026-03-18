from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.utils import generate_uuid


class WhatsAppAccount(Base):
    __tablename__ = "whatsapp_accounts"

    id = Column(String, primary_key=True, default=generate_uuid)

    tenant_id = Column(
        String,
        ForeignKey("tenants.id"),
        nullable=False
    )

    # Seller's visible WhatsApp number
    phone_number = Column(
        String,
        nullable=False,
        unique=True
    )

    # Meta internal identifier used in webhook routing
    phone_number_id = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    tenant = relationship(
        "Tenant",
        back_populates="whatsapp_accounts"
    )