# app/services/transaction_service.py

from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
from app.schemas.transaction import (
    FinalizeTransactionResponse,
    FinalizeTransactionItemSummary,
)
import uuid
import logging
from decimal import Decimal, ROUND_HALF_UP
from app.core.datetime_utils import get_start_of_day, get_end_of_day

logger = logging.getLogger(__name__)


def create_transaction(db: Session, seller_phone: str, tenant_id: str) -> Transaction:
    """
    Create a new transaction for a seller.
    """
    tx = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        seller_phone=seller_phone,
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
    unit_price: Decimal,
    cost_per_unit: Optional[Decimal] = None,
) -> TransactionItem:
    """
    Add a product line to a transaction.
    Calculates total_amount and profit (if cost_per_unit provided).
    Updates transaction total_amount after each item.
    """
    # --- Validate transaction exists and belongs to tenant ---
    transaction = db.query(Transaction).filter_by(
        id=transaction_id,
        tenant_id=tenant_id,
    ).first()

    if not transaction:
        logger.error(f"Transaction not found: id={transaction_id}, tenant={tenant_id}")
        raise ValueError(
            f"Transaction {transaction_id} not found or does not belong to tenant {tenant_id}"
        )

    # --- Coerce to Decimal for safe financial arithmetic ---
    quantity_dec = Decimal(quantity)
    unit_price_dec = Decimal(str(unit_price))
    cost_per_unit_dec = Decimal(str(cost_per_unit)) if cost_per_unit is not None else None

    total_amount = (quantity_dec * unit_price_dec).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # profit = (unit_price - cost_per_unit) * quantity
    profit = (
        ((unit_price_dec - cost_per_unit_dec) * quantity_dec).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if cost_per_unit_dec is not None
        else None
    )

    # --- Create item ---
    item = TransactionItem(
        id=str(uuid.uuid4()),
        transaction_id=transaction_id,
        tenant_id=tenant_id,
        product_name=product_name,
        quantity=int(quantity_dec),
        unit_price=unit_price_dec,
        total_amount=total_amount,
        cost_per_unit=cost_per_unit_dec,
        profit=profit,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # --- Update transaction total_amount ---
    db.refresh(transaction)
    transaction.total_amount = sum(i.total_amount for i in transaction.items)
    db.commit()

    logger.info(f"Item added: {product_name} x{quantity} → {total_amount} RWF | profit={profit}")
    return item


def _calculate_profit_fields(
    items: list[TransactionItem],
) -> tuple[Optional[Decimal], bool, int]:
    """
    Derives profit summary fields from a list of transaction items.

    Returns:
        total_profit: sum of profit for tracked items, or None if no items have cost
        profit_complete: True only if all items have cost_per_unit
        items_missing_cost_count: number of items without cost_per_unit
    """
    tracked = [i for i in items if i.cost_per_unit is not None]
    missing = [i for i in items if i.cost_per_unit is None]

    total_profit = (
        sum(i.profit for i in tracked if i.profit is not None)
        if tracked
        else None
    )
    profit_complete = len(missing) == 0
    items_missing_cost_count = len(missing)

    return total_profit, profit_complete, items_missing_cost_count


def finalize_transaction(
    db: Session,
    transaction_id: str,
    tenant_id: str,
) -> FinalizeTransactionResponse:
    """
    Finalizes a transaction:
    - Computes and persists profit summary fields on the transaction
    - Returns structured FinalizeTransactionResponse for the handler to format

    Note: conversation state reset is the caller's responsibility.
    """
    transaction = db.query(Transaction).filter_by(
        id=transaction_id,
        tenant_id=tenant_id,
    ).first()

    if not transaction:
        raise ValueError(
            f"Transaction {transaction_id} not found or does not belong to tenant {tenant_id}"
        )

    items = transaction.items
    if not items:
        raise ValueError(f"Transaction {transaction_id} has no items")

    # --- Calculate and persist profit fields ---
    total_profit, profit_complete, items_missing_cost_count = _calculate_profit_fields(items)

    transaction.total_profit = total_profit
    transaction.profit_complete = profit_complete
    transaction.items_missing_cost_count = items_missing_cost_count
    db.commit()
    db.refresh(transaction)

    logger.info(
        f"Transaction finalized: id={transaction_id} | "
        f"total={transaction.total_amount} | profit={total_profit} | "
        f"complete={profit_complete} | missing={items_missing_cost_count}"
    )

    # --- Build structured response ---
    return FinalizeTransactionResponse(
        transaction_id=transaction.id,
        total_amount=transaction.total_amount,
        total_profit=total_profit,
        profit_complete=profit_complete,
        items_missing_cost_count=items_missing_cost_count,
        items=[
            FinalizeTransactionItemSummary(
                product_name=i.product_name,
                quantity=i.quantity,
                unit_price=i.unit_price,
                total_amount=i.total_amount,
                cost_per_unit=i.cost_per_unit,
                profit=i.profit,
            )
            for i in items
        ],
    )


def set_product_cost(
    db: Session,
    tenant_id: str,
    product_name: str,
    cost_per_unit: Decimal,
    target_date: date,
) -> Optional[dict]:
    """
    Retroactively set cost_per_unit for all items of a product sold today.
    Recalculates profit on each item and updates parent transaction profit fields.
    Returns None if no matching items found today.
    """
    start = get_start_of_day(target_date)
    end = get_end_of_day(target_date)

    items = (
        db.query(TransactionItem)
        .join(Transaction, TransactionItem.transaction_id == Transaction.id)
        .filter(
            TransactionItem.tenant_id == tenant_id,
            TransactionItem.product_name.ilike(product_name),
            Transaction.created_at >= start,
            Transaction.created_at <= end,
        )
        .all()
    )

    if not items:
        return None

    product_profit = Decimal("0")
    affected_tx_ids: set[str] = set()

    for item in items:
        item.cost_per_unit = cost_per_unit
        item.profit = (
            (item.unit_price - cost_per_unit) * item.quantity
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        product_profit += item.profit
        affected_tx_ids.add(item.transaction_id)

    db.flush()

    # Refresh profit fields on each affected transaction
    for tx_id in affected_tx_ids:
        tx = db.query(Transaction).filter_by(id=tx_id, tenant_id=tenant_id).first()
        if tx:
            db.refresh(tx)
            total_p, complete, missing_count = _calculate_profit_fields(tx.items)
            tx.total_profit = total_p
            tx.profit_complete = complete
            tx.items_missing_cost_count = missing_count

    db.commit()

    logger.info(
        f"set_product_cost: product={items[0].product_name} | "
        f"cost={cost_per_unit} | items={len(items)} | profit={product_profit}"
    )

    return {
        "product_name": items[0].product_name,  # preserve original casing
        "product_profit": product_profit,
    }