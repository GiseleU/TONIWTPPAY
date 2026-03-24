from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.utils import generate_uuid


class Product(Base):
    __tablename__ = "products"

    # ---- Core fields ----
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)

    # Optional fields for profit tracking
    price_per_unit = Column(Numeric(12, 2), nullable=True)  # last known selling price
    cost_per_unit = Column(Numeric(12, 2), nullable=True)   # optional → enables profit tracking

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ---- Relationships ----
    tenant = relationship("Tenant", back_populates="products")

    # ---- Constraints ----
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_product_tenant_name"),
    )