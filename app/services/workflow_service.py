# app/services/workflow_service.py
"""
Workflow State Machine Service

Orchestrates the complete order workflow from inquiry to payment.
Handles state transitions and maintains workflow session state.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import uuid

from app.models.workflow_session import WorkflowSession
from app.models.inquiry import Inquiry
from app.models.order import Order
from app.models.order_line_item import OrderLineItem
from app.models.event import Event
from app.core.enums import WorkflowState, EventType, ActorType


class WorkflowError(Exception):
    """Raised when workflow state transition is invalid."""
    pass


# In-memory storage for products being entered (per session)
# Key: session_id, Value: List of {"product_name": str, "quantity": int, "price": int}
_products_cache: Dict[str, List[Dict[str, Any]]] = {}


# Allowed workflow state transitions
WORKFLOW_TRANSITIONS = {
    WorkflowState.AWAITING_CONFIRM: [WorkflowState.ENTERING_PRODUCTS, WorkflowState.CANCELLED],
    WorkflowState.ENTERING_PRODUCTS: [WorkflowState.ORDER_SUMMARY, WorkflowState.CANCELLED],
    WorkflowState.ORDER_SUMMARY: [WorkflowState.AWAITING_PAYMENT, WorkflowState.ENTERING_PRODUCTS, WorkflowState.CANCELLED],
    WorkflowState.AWAITING_PAYMENT: [WorkflowState.COMPLETED, WorkflowState.CANCELLED],
    WorkflowState.COMPLETED: [],
    WorkflowState.CANCELLED: [WorkflowState.AWAITING_CONFIRM],
}


def _validate_transition(current_state: WorkflowState, new_state: WorkflowState) -> bool:
    """Validate if workflow state transition is allowed."""
    allowed_states = WORKFLOW_TRANSITIONS.get(current_state, [])
    return new_state in allowed_states


def _record_event(
    db: Session,
    tenant_id: str,
    event_type: EventType,
    actor: ActorType,
    inquiry_id: str,
    order_id: Optional[str] = None,
    session_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None
) -> Event:
    """Record a workflow event."""
    event = Event(
        id=str(uuid.uuid4()),
        event_type=event_type,
        actor=actor,
        tenant_id=tenant_id,
        inquiry_id=inquiry_id,
        order_id=order_id,
        payload=payload or {}
    )
    db.add(event)
    return event


def start_workflow(inquiry_id: str, seller_phone: str, db: Session) -> Dict[str, Any]:
    """
    Start a new workflow session for an inquiry.
    
    Creates a WorkflowSession and transitions to ENTERING_PRODUCTS state.
    
    Args:
        inquiry_id: The inquiry ID to start workflow for
        seller_phone: Seller's phone number
        db: Database session
        
    Returns:
        Dict with workflow session info and message
        
    Raises:
        WorkflowError: If transition is not allowed
        ValueError: If inquiry not found
    """
    # Get inquiry
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise ValueError(f"Inquiry not found: {inquiry_id}")
    
    tenant_id = inquiry.tenant_id
    
    # Check if workflow session already exists
    existing_session = db.query(WorkflowSession).filter(
        WorkflowSession.inquiry_id == inquiry_id,
        WorkflowSession.workflow_state.in_([
            WorkflowState.AWAITING_CONFIRM,
            WorkflowState.ENTERING_PRODUCTS,
            WorkflowState.ORDER_SUMMARY,
            WorkflowState.AWAITING_PAYMENT,
        ])
    ).first()
    
    if existing_session:
        # Resume existing session
        session = existing_session
    else:
        # Create new workflow session
        session = WorkflowSession(
            id=WorkflowSession.generate_id(),
            seller_phone=seller_phone,
            inquiry_id=inquiry_id,
            workflow_state=WorkflowState.AWAITING_CONFIRM,
        )
        db.add(session)
    
    # Validate and perform transition: AWAITING_CONFIRM → ENTERING_PRODUCTS
    if not _validate_transition(session.workflow_state, WorkflowState.ENTERING_PRODUCTS):
        raise WorkflowError(f"Cannot start workflow from state: {session.workflow_state}")
    
    # Transition to ENTERING_PRODUCTS
    session.workflow_state = WorkflowState.ENTERING_PRODUCTS
    
    # Update inquiry status
    inquiry.status = "confirmed"
    
    # Record event
    _record_event(
        db=db,
        tenant_id=tenant_id,
        event_type=EventType.INQUIRY_CONFIRMED,
        actor=ActorType.SELLER,
        inquiry_id=inquiry_id,
        session_id=session.id,
        payload={"seller_phone": seller_phone}
    )
    
    db.commit()
    
    return {
        "status": "ok",
        "session_id": session.id,
        "inquiry_id": inquiry_id,
        "workflow_state": session.workflow_state.value,
        "message": "Order workflow started. Please enter products: Product Name Quantity Price (e.g., Juice 2 800)"
    }


def add_product(session_id: str, product_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Add a product to the current workflow session.
    
    Args:
        session_id: The workflow session ID
        product_data: Dict with product_name, quantity, price
        db: Database session
        
    Returns:
        Dict with product info and running total
        
    Raises:
        WorkflowError: If session not in ENTERING_PRODUCTS state
    """
    # Get session
    session = db.query(WorkflowSession).filter(WorkflowSession.id == session_id).first()
    if not session:
        raise WorkflowError(f"Workflow session not found: {session_id}")
    
    # Validate state: must be in ENTERING_PRODUCTS
    if session.workflow_state != WorkflowState.ENTERING_PRODUCTS:
        raise WorkflowError(f"Cannot add products in state: {session.workflow_state}. Type DONE to finish.")
    
    # Add product to cache
    if session_id not in _products_cache:
        _products_cache[session_id] = []
    
    _products_cache[session_id].append(product_data)
    
    # Calculate running total
    products = _products_cache[session_id]
    total = sum(p["quantity"] * p["price"] for p in products)
    
    return {
        "status": "ok",
        "action": "product_added",
        "product": product_data,
        "products_count": len(products),
        "running_total": total,
        "message": f"{product_data['product_name']} added! (Qty: {product_data['quantity']}, Price: {product_data['price']})\nHari ikindi gicuruzwa? (Type another product or DONE to finish)"
    }


def generate_summary(session_id: str, db: Session) -> Dict[str, Any]:
    """
    Generate order summary and create order with line items.
    
    Transitions to ORDER_SUMMARY state.
    
    Args:
        session_id: The workflow session ID
        db: Database session
        
    Returns:
        Dict with order summary and message
        
    Raises:
        WorkflowError: If no products added or invalid state
    """
    # Get session
    session = db.query(WorkflowSession).filter(WorkflowSession.id == session_id).first()
    if not session:
        raise WorkflowError(f"Workflow session not found: {session_id}")
    
    # Validate state: must be in ENTERING_PRODUCTS
    if session.workflow_state != WorkflowState.ENTERING_PRODUCTS:
        raise WorkflowError(f"Cannot generate summary in state: {session.workflow_state}")
    
    # Get products from cache
    products = _products_cache.get(session_id, [])
    if not products:
        raise WorkflowError("No products entered. Please add at least one product.")
    
    # Calculate total
    total = sum(p["quantity"] * p["price"] for p in products)
    
    # Get inquiry for context
    inquiry = db.query(Inquiry).filter(Inquiry.id == session.inquiry_id).first()
    tenant_id = inquiry.tenant_id if inquiry else None
    
    # Create order
    order = Order(
        id=f"O{uuid.uuid4().hex[:8].upper()}",
        tenant_id=tenant_id,
        contact_id=inquiry.contact_id if inquiry else None,
        inquiry_id=session.inquiry_id,
        amount=total,
        customer_name=inquiry.message if inquiry else "Unknown",  # Use inquiry message as customer name
        customer_phone=inquiry.contact.phone_number if inquiry and inquiry.contact else "Unknown",
        status="pending",
    )
    db.add(order)
    
    # Create line items
    for product_data in products:
        line_item = OrderLineItem(
            id=f"LI{uuid.uuid4().hex[:8].upper()}",
            order_id=order.id,
            product_name=product_data["product_name"],
            quantity=product_data["quantity"],
            unit_price=product_data["price"],
            total_price=product_data["quantity"] * product_data["price"],
        )
        db.add(line_item)
    
    # Link order to session
    session.order_id = order.id
    
    # Validate and perform transition: ENTERING_PRODUCTS → ORDER_SUMMARY
    if not _validate_transition(session.workflow_state, WorkflowState.ORDER_SUMMARY):
        raise WorkflowError(f"Cannot transition from {session.workflow_state} to ORDER_SUMMARY")
    
    session.workflow_state = WorkflowState.ORDER_SUMMARY
    
    # Generate summary message
    summary_lines = ["Order Summary:"]
    for p in products:
        line_total = p["quantity"] * p["price"]
        summary_lines.append(f"{p['product_name']} — {p['quantity']} × {p['price']} = {line_total} RWF")
    summary_lines.append(f"TOTAL = {total} RWF")
    summary_lines.append("")
    summary_lines.append("Ese ibi ni byo?")
    
    # Record event
    if tenant_id:
        _record_event(
            db=db,
            tenant_id=tenant_id,
            event_type=EventType.ORDER_CREATED,
            actor=ActorType.SELLER,
            inquiry_id=session.inquiry_id,
            order_id=order.id,
            session_id=session.id,
            payload={"products": products, "total": total}
        )
    
    db.commit()
    
    return {
        "status": "ok",
        "action": "order_summary",
        "session_id": session.id,
        "order_id": order.id,
        "products": products,
        "total": total,
        "message": "\n".join(summary_lines)
    }


def confirm_order(session_id: str, db: Session) -> Dict[str, Any]:
    """
    Confirm the order and transition to awaiting payment.
    
    Args:
        session_id: The workflow session ID
        db: Database session
        
    Returns:
        Dict with confirmation message
        
    Raises:
        WorkflowError: If session not in ORDER_SUMMARY state
    """
    # Get session
    session = db.query(WorkflowSession).filter(WorkflowSession.id == session_id).first()
    if not session:
        raise WorkflowError(f"Workflow session not found: {session_id}")
    
    # Validate state: must be in ORDER_SUMMARY
    if session.workflow_state != WorkflowState.ORDER_SUMMARY:
        raise WorkflowError(f"Cannot confirm order in state: {session.workflow_state}")
    
    # Validate and perform transition: ORDER_SUMMARY → AWAITING_PAYMENT
    if not _validate_transition(session.workflow_state, WorkflowState.AWAITING_PAYMENT):
        raise WorkflowError(f"Cannot transition from {session.workflow_state} to AWAITING_PAYMENT")
    
    session.workflow_state = WorkflowState.AWAITING_PAYMENT
    
    # Get inquiry for tenant_id
    inquiry = db.query(Inquiry).filter(Inquiry.id == session.inquiry_id).first()
    tenant_id = inquiry.tenant_id if inquiry else None
    
    # Record event
    if tenant_id:
        _record_event(
            db=db,
            tenant_id=tenant_id,
            event_type=EventType.ORDER_CREATED,
            actor=ActorType.SELLER,
            inquiry_id=session.inquiry_id,
            order_id=session.order_id,
            session_id=session.id,
            payload={"action": "confirm"}
        )
    
    db.commit()
    
    return {
        "status": "ok",
        "action": "order_confirmed",
        "session_id": session.id,
        "workflow_state": session.workflow_state.value,
        "message": "Order confirmed! Ask customer to pay. When payment is received, type PAID."
    }


def record_payment(session_id: str, db: Session) -> Dict[str, Any]:
    """
    Record payment and complete the workflow.
    
    Args:
        session_id: The workflow session ID
        db: Database session
        
    Returns:
        Dict with completion message
        
    Raises:
        WorkflowError: If session not in AWAITING_PAYMENT state
    """
    # Get session
    session = db.query(WorkflowSession).filter(WorkflowSession.id == session_id).first()
    if not session:
        raise WorkflowError(f"Workflow session not found: {session_id}")
    
    # Validate state: must be in AWAITING_PAYMENT
    if session.workflow_state != WorkflowState.AWAITING_PAYMENT:
        raise WorkflowError(f"Cannot record payment in state: {session.workflow_state}")
    
    # Validate and perform transition: AWAITING_PAYMENT → COMPLETED
    if not _validate_transition(session.workflow_state, WorkflowState.COMPLETED):
        raise WorkflowError(f"Cannot transition from {session.workflow_state} to COMPLETED")
    
    session.workflow_state = WorkflowState.COMPLETED
    
    # Update order status
    if session.order:
        session.order.status = "paid"
    
    # Get inquiry for tenant_id
    inquiry = db.query(Inquiry).filter(Inquiry.id == session.inquiry_id).first()
    tenant_id = inquiry.tenant_id if inquiry else None
    
    # Record event
    if tenant_id:
        _record_event(
            db=db,
            tenant_id=tenant_id,
            event_type=EventType.PAYMENT_RECORDED,
            actor=ActorType.SELLER,
            inquiry_id=session.inquiry_id,
            order_id=session.order_id,
            session_id=session.id,
            payload={"action": "paid"}
        )
    
    db.commit()
    
    return {
        "status": "ok",
        "action": "payment_recorded",
        "session_id": session.id,
        "workflow_state": session.workflow_state.value,
        "message": "Payment recorded! Order is complete. Thank you!"
    }


def cancel_workflow(session_id: str, db: Session) -> Dict[str, Any]:
    """
    Cancel the workflow and reset to initial state.
    
    Args:
        session_id: The workflow session ID
        db: Database session
        
    Returns:
        Dict with cancellation message
    """
    # Get session
    session = db.query(WorkflowSession).filter(WorkflowSession.id == session_id).first()
    if not session:
        raise WorkflowError(f"Workflow session not found: {session_id}")
    
    inquiry_id = session.inquiry_id
    
    # Get inquiry for tenant_id
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    tenant_id = inquiry.tenant_id if inquiry else None
    
    # Cancel current session - transition to CANCELLED
    if session.workflow_state != WorkflowState.CANCELLED:
        if _validate_transition(session.workflow_state, WorkflowState.CANCELLED):
            session.workflow_state = WorkflowState.CANCELLED
            
            # Record event
            if tenant_id:
                _record_event(
                    db=db,
                    tenant_id=tenant_id,
                    event_type=EventType.INQUIRY_DROPPED,
                    actor=ActorType.SELLER,
                    inquiry_id=inquiry_id,
                    session_id=session.id,
                    payload={"action": "cancelled"}
                )
    
    # Clear products cache
    if session_id in _products_cache:
        del _products_cache[session_id]
    
    db.commit()
    
    return {
        "status": "ok",
        "action": "workflow_cancelled",
        "session_id": session.id,
        "workflow_state": session.workflow_state.value,
        "message": "Order cancelled. Type CONFIRM to start a new order."
    }


def get_session_products(session_id: str) -> List[Dict[str, Any]]:
    """Get products stored in cache for a session."""
    return _products_cache.get(session_id, [])


def clear_session_products(session_id: str) -> None:
    """Clear products from cache for a session."""
    if session_id in _products_cache:
        del _products_cache[session_id]
