from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.utils import generate_uuid

class Payment(Base):
    """
    Payment record for a transaction.
    """

    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(String, nullable=False)  # e.g., 'cash', 'bank', 'momo'
    verified_by = Column(String, nullable=True)  # optional actor
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="payments")
    transaction = relationship("Transaction", back_populates="payments")