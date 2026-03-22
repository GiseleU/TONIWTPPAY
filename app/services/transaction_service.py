# app/services/transaction_service.py
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
import uuid
from decimal import Decimal, ROUND_HALF_UP
from app.services.state_service import reset_state


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
    unit_price: float
) -> TransactionItem:
    """
    Add a product line to a transaction.

    Automatically calculates total_amount = quantity * unit_price
    and updates the transaction's total.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # --- Validate Transaction exists and belongs to tenant ---
    logger.info(f"Looking for transaction: id={transaction_id}, tenant={tenant_id}")
    transaction = db.query(Transaction).filter_by(
        id=transaction_id, 
        tenant_id=tenant_id
    ).first()
    
    logger.info(f"Transaction found: {transaction is not None}")
    if not transaction:
        logger.error(f"Transaction NOT FOUND: id={transaction_id}, tenant={tenant_id}")
        raise ValueError(
            f"Transaction {transaction_id} not found or does not belong to tenant {tenant_id}"
        )
    
    logger.info(f"Transaction OK: {transaction.id}, total_items_before={len(transaction.items)}")

    # --- Convert to Decimal for accurate financial calculation ---
    quantity_dec = Decimal(quantity)
    unit_price_dec = Decimal(str(unit_price))
    total_amount = (quantity_dec * unit_price_dec).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # --- Create TransactionItem ---
    item = TransactionItem(
        id=str(uuid.uuid4()),
        transaction_id=transaction_id,
        tenant_id=tenant_id,
        product_name=product_name,
        quantity=int(quantity_dec),
        unit_price=unit_price_dec,
        total_amount=total_amount
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # --- Refresh transaction to load new item in relationship ---
    db.refresh(transaction)
    
    # --- Update Transaction total_amount ---
    transaction_total = sum(i.total_amount for i in transaction.items)
    transaction.total_amount = transaction_total
    db.commit()
    db.refresh(transaction)
    
    logger.info(f"Item added successfully: {product_name}, new total={transaction.total_amount}")
    return item


# --------------------------
# Finalize Transaction
# --------------------------
def finalize_transaction(db: Session, transaction_id: str, state) -> str:
    """
    Finalizes a transaction, returns a summary text, and resets conversation state.
    """
    items = db.query(TransactionItem).filter_by(transaction_id=transaction_id).all()
    if not items:
        raise ValueError("No items in transaction")

    total = sum(i.total_amount for i in items)
    summary_lines = [
        f"- {i.product_name} x{i.quantity} @ {i.unit_price} → {i.total_amount} RWF"
        for i in items
    ]
    summary_lines.append(f"\n💰 Total: {total} RWF")
    summary_text = "✅ Sale recorded\n" + "Items:\n" + "\n".join(summary_lines)

    # Reset conversation state
    reset_state(state, db)

    return summary_text