from sqlalchemy import Column, String, DateTime, ForeignKey
import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.utils import generate_uuid

class Transaction(Base):
    """
    Transaction representing a sale by a seller (multi-product).
    """

    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    seller_phone = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ---- Relationships ----
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="transaction", cascade="all, delete-orphan")
    tenant = relationship("Tenant", back_populates="transactions")
