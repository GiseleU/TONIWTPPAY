# app/models/product.py

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Product(Base):
    """
    Represents a product in the seller's catalog.
    
    Used for Click Selection mode when entering products.
    """

    __tablename__ = "products"

    # ---- Identity ----
    id = Column(String, primary_key=True)  # P####
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)

    # ---- Product Details ----
    name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # ---- Timestamps ----
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ---- Relationships ----
    tenant = relationship("Tenant", back_populates="products")
