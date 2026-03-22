from sqlalchemy import Column, String, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.utils import generate_uuid

class TransactionItem(Base):
    """
    Represents a single product line in a Transaction (multi-product sale).
    """

    __tablename__ = "transaction_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)  # total for this item (quantity * unit price)

    # ---- Relationships ----
    transaction = relationship("Transaction", back_populates="items")
    tenant = relationship("Tenant", back_populates="transaction_items")
