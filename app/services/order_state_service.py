# app/services/order_state_service.py

import uuid
from sqlalchemy.orm import Session
from app.models.inquiry import Inquiry
from app.models.order import Order
from app.models.event import Event
from app.core.enums import EventType, ActorType


class OrderStateError(Exception):
    """Raised when an order state transition is invalid."""
    pass


def create_order_from_inquiry(
    *,
    inquiry_id: str,
    tenant_id: str,
    customer_name: str,
    customer_phone: str,
    customer_address: str | None,
    db: Session,
) -> Order:
    """
    Deterministically converts a CONFIRMED inquiry into an Order.

    Preconditions:
      - Inquiry exists
      - Inquiry belongs to tenant
      - Inquiry status == 'confirmed'
      - Inquiry has amount set
      - Required customer fields provided
      - Inquiry has no existing order

    Postconditions:
      - Order is created exactly once
      - Inquiry is linked to order
      - ORDER_CREATED event is recorded
      - Inquiry status updated to 'completed'
    """

    # ---- Fetch inquiry ----
    inquiry = (
        db.query(Inquiry)
        .filter_by(id=inquiry_id, tenant_id=tenant_id)
        .first()
    )

    if not inquiry:
        raise OrderStateError(f"Inquiry {inquiry_id} not found")

    # ---- Duplicate check first ----
    if inquiry.order:
        raise OrderStateError(f"Inquiry {inquiry_id} already has an order")

    # ---- State validation ----
    if inquiry.status != "confirmed":
        raise OrderStateError(
            f"Inquiry {inquiry_id} must be confirmed before order creation"
        )

    if inquiry.amount is None:
        raise OrderStateError(
            f"Inquiry {inquiry_id} has no confirmed amount"
        )

    # ---- Customer data validation ----
    if not customer_name:
        raise OrderStateError("Customer name is required")

    if not customer_phone:
        raise OrderStateError("Customer phone is required")

    # ---- Create order ----
    order = Order(
        id=f"O{uuid.uuid4().hex[:8].upper()}",
        tenant_id=tenant_id,
        inquiry_id=inquiry.id,
        contact_id=inquiry.contact_id,
        amount=inquiry.amount,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_address=customer_address,
    )

    db.add(order)

    # ---- Audit event ----
    event = Event(
        id=str(uuid.uuid4()),
        event_type=EventType.ORDER_CREATED,
        actor=ActorType.SYSTEM,
        tenant_id=tenant_id,
        inquiry_id=inquiry.id,
        order_id=order.id,
        payload={
            "amount": str(order.amount),
            "customer_phone": customer_phone,
        },
    )
    db.add(event)

    # ---- Update inquiry ----
    inquiry.status = "completed"
    db.commit()

    return order