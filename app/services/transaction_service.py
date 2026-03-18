# app/services/transaction_service.py
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
import uuid


def create_transaction(db: Session, seller_phone: str, tenant_id: str) -> Transaction:
    """
    Create a new transaction for a seller.
    """
    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        seller_phone=seller_phone
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def add_item(
    db: Session,
    transaction_id: str,
    tenant_id: str,
    product_name: str,
    quantity: int,
    total_amount: float
) -> TransactionItem:
    """
    Add a product line to a transaction.
    """
    item = TransactionItem(
        id=str(uuid.uuid4()),
        transaction_id=transaction_id,
        tenant_id=tenant_id,
        product_name=product_name,
        quantity=quantity,
        total_amount=total_amount
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item