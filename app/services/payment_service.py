# app/services/payment_service.py

from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.payment import Payment
from app.models.order import Order
from app.models.event import Event
from app.core.enums import EventType, ActorType
from uuid import uuid4

class PaymentError(Exception):
    """Custom exception for payment failures."""
    pass


def record_manual_payment(
    *,
    order_id: str,
    amount: Decimal,
    verified_by: str,
    method: str,
    notes: str | None = None,
    db: Session,
) -> Payment:
    """
    Record a manual payment for an order.

    - Validates order exists and is in 'completed' status.
    - Prevents overpayments (total paid cannot exceed order amount).
    - Prevents duplicate payments (exact same amount already recorded).
    - Creates immutable payment record.
    - Updates order status to 'paid' if fully reconciled.
    - Logs PAYMENT_RECORDED or PAYMENT_FAILED event.
    """
    # Fetch order
    order = db.get(Order, order_id)
    if not order:
        raise PaymentError(f"Order {order_id} not found")

    if order.status != "completed":
        raise PaymentError(f"Order {order_id} must be in 'completed' status to record payment")

    # Check for overpayment
    current_total = order.total_paid
    if current_total + amount > order.amount:
        raise PaymentError(f"Payment of {amount} would exceed order total. Current paid: {current_total}, Order amount: {order.amount}")

    # Check for duplicate (exact same amount already recorded)
    existing = (
        db.query(Payment)
        .filter(Payment.order_id == order_id)
        .filter(Payment.amount == amount)
        .first()
    )
    if existing:
        raise PaymentError(f"Duplicate payment of {amount} already recorded for order {order_id}")

    # Create immutable Payment record
    payment = Payment(
        id=f"P{uuid4().hex[:8].upper()}",
        tenant_id=order.tenant_id,
        order_id=order_id,
        amount=amount,
        verified_by=verified_by,
        method=method,
        notes=notes,
    )

    db.add(payment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise PaymentError("Failed to record payment due to database integrity error")

    # Update order status if fully paid
    if order.is_fully_paid():
        order.status = "paid"
        db.add(order)
        db.commit()

    # Log PAYMENT_RECORDED event
    event = Event(
        id=f"E{uuid4().hex[:8].upper()}",
        event_type=EventType.PAYMENT_RECORDED,
        actor=ActorType.SELLER,  # Assuming verified_by is seller/admin
        tenant_id=order.tenant_id,
        order_id=order_id,
        payment_id=payment.id,
        payload={
            "message": f"Manual payment of {amount} recorded for order {order_id} by {verified_by}",
            "method": method,
            "notes": notes,
        },
    )
    db.add(event)
    db.commit()

    return payment
