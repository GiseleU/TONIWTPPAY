# app/services/order_state_service.py

import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.inquiry import Inquiry
from app.models.order import Order
from app.models.order_line_item import OrderLineItem
from app.models.workflow_session import WorkflowSession
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


def create_order_with_line_items(
    *,
    inquiry_id: str,
    tenant_id: str,
    customer_name: str,
    customer_phone: str,
    customer_address: Optional[str],
    line_items: List[Dict[str, Any]],
    workflow_session_id: Optional[str] = None,
    db: Session,
) -> Order:
    """
    Creates an Order with line items from workflow data.

    This function is used by the workflow to create orders with
    multiple products (line items) instead of a single amount.

    Args:
        inquiry_id: The inquiry ID
        tenant_id: The tenant ID
        customer_name: Customer's name
        customer_phone: Customer's phone number
        customer_address: Optional customer address
        line_items: List of dicts with product_name, quantity, unit_price
        workflow_session_id: Optional workflow session ID to link
        db: Database session

    Returns:
        Created Order with line items

    Raises:
        OrderStateError: If validation fails
    """
    # ---- Fetch inquiry ----
    inquiry = (
        db.query(Inquiry)
        .filter_by(id=inquiry_id, tenant_id=tenant_id)
        .first()
    )

    if not inquiry:
        raise OrderStateError(f"Inquiry {inquiry_id} not found")

    # ---- Validate line items ----
    if not line_items:
        raise OrderStateError("At least one line item is required")

    # ---- Calculate total amount ----
    total_amount = sum(
        item["quantity"] * item["unit_price"] for item in line_items
    )

    # ---- Create order ----
    order = Order(
        id=f"O{uuid.uuid4().hex[:8].upper()}",
        tenant_id=tenant_id,
        inquiry_id=inquiry.id,
        contact_id=inquiry.contact_id,
        amount=total_amount,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_address=customer_address,
        status="pending",
    )

    db.add(order)

    # ---- Create line items ----
    for item in line_items:
        line_item = OrderLineItem(
            id=f"LI{uuid.uuid4().hex[:8].upper()}",
            order_id=order.id,
            product_name=item["product_name"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            total_price=item["quantity"] * item["unit_price"],
        )
        db.add(line_item)

    # ---- Link to workflow session if provided ----
    if workflow_session_id:
        workflow_session = (
            db.query(WorkflowSession)
            .filter(WorkflowSession.id == workflow_session_id)
            .first()
        )
        if workflow_session:
            workflow_session.order_id = order.id

    # ---- Audit event ----
    event = Event(
        id=str(uuid.uuid4()),
        event_type=EventType.ORDER_CREATED,
        actor=ActorType.SYSTEM,
        tenant_id=tenant_id,
        inquiry_id=inquiry.id,
        order_id=order.id,
        payload={
            "amount": str(total_amount),
            "customer_phone": customer_phone,
            "line_items_count": len(line_items),
            "workflow_session_id": workflow_session_id,
        },
    )
    db.add(event)

    # ---- Update inquiry status ----
    inquiry.status = "completed"

    db.commit()

    return order


def link_order_to_workflow(
    *,
    order_id: str,
    workflow_session_id: str,
    db: Session,
) -> WorkflowSession:
    """
    Link an existing order to a workflow session.

    Args:
        order_id: The order ID
        workflow_session_id: The workflow session ID
        db: Database session

    Returns:
        Updated WorkflowSession

    Raises:
        OrderStateError: If order or session not found
    """
    # Get workflow session
    workflow_session = (
        db.query(WorkflowSession)
        .filter(WorkflowSession.id == workflow_session_id)
        .first()
    )

    if not workflow_session:
        raise OrderStateError(f"Workflow session {workflow_session_id} not found")

    # Get order
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise OrderStateError(f"Order {order_id} not found")

    # Link order to workflow session
    workflow_session.order_id = order_id

    db.commit()

    return workflow_session
