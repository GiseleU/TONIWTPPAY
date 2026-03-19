from sqlalchemy import Column, String, DateTime, Enum as PgEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.utils import generate_uuid
from app.core.enums import CoexistenceStatus
from app.models.transaction import Transaction

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=True)  # Seller's personal WhatsApp for notifications
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    coexistence_status = Column(
        PgEnum(CoexistenceStatus),
        nullable=False,
        default=CoexistenceStatus.PENDING
    )  # Only ACTIVE tenants can send/receive messages.

    # ---- Relationships ----

    transactions = relationship(
        Transaction, back_populates="tenant", cascade="all, delete-orphan"
    )
    transaction_items = relationship(
        "TransactionItem", back_populates="tenant", cascade="all, delete-orphan"
    )
    payments = relationship(
        "Payment", back_populates="tenant", cascade="all, delete-orphan"
    )
    daily_summaries = relationship(
        "DailySummary", back_populates="tenant", cascade="all, delete-orphan"
    )
    events = relationship(
        "Event", back_populates="tenant", cascade="all, delete-orphan"
    )
