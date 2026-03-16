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


# NOTE:
# In-memory cache used for MVP simplicity.
# If server restarts, product entry state is lost.
# In production this should move to Redis.
_products_cache: Dict[str, List[Dict[str, Any]]] = {}


WORKFLOW_TRANSITIONS = {
    WorkflowState.AWAITING_CONFIRM: [WorkflowState.ENTERING_PRODUCTS, WorkflowState.CANCELLED],
    WorkflowState.ENTERING_PRODUCTS: [WorkflowState.ORDER_SUMMARY, WorkflowState.CANCELLED],
    WorkflowState.ORDER_SUMMARY: [WorkflowState.AWAITING_PAYMENT, WorkflowState.ENTERING_PRODUCTS, WorkflowState.CANCELLED],
    WorkflowState.AWAITING_PAYMENT: [WorkflowState.COMPLETED, WorkflowState.CANCELLED],
    WorkflowState.COMPLETED: [],
    WorkflowState.CANCELLED: [WorkflowState.AWAITING_CONFIRM],
}


def _validate_transition(current_state: WorkflowState, new_state: WorkflowState) -> bool:
    allowed = WORKFLOW_TRANSITIONS.get(current_state, [])
    return new_state in allowed


def _record_event(
    db: Session,
    tenant_id: str,
    event_type: EventType,
    actor: ActorType,
    inquiry_id: str,
    order_id: Optional[str] = None,
    session_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Event:

    event = Event(
        id=str(uuid.uuid4()),
        event_type=event_type,
        actor=actor,
        tenant_id=tenant_id,
        inquiry_id=inquiry_id,
        order_id=order_id,
        session_id=session_id,
        payload=payload or {},
    )

    db.add(event)
    return event


# ---------------------------------------------------------
# START WORKFLOW
# ---------------------------------------------------------
def start_workflow(inquiry_id: str, seller_phone: str, db: Session) -> Dict[str, Any]:

    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise ValueError(f"Inquiry not found: {inquiry_id}")

    tenant_id = inquiry.tenant_id

    try:

        existing_session = db.query(WorkflowSession).filter(
            WorkflowSession.inquiry_id == inquiry_id,
            WorkflowSession.workflow_state.in_(
                [
                    WorkflowState.AWAITING_CONFIRM,
                    WorkflowState.ENTERING_PRODUCTS,
                    WorkflowState.ORDER_SUMMARY,
                    WorkflowState.AWAITING_PAYMENT,
                ]
            ),
        ).first()

        if existing_session:
            session = existing_session
        else:
            session = WorkflowSession(
                id=WorkflowSession.generate_id(),
                seller_phone=seller_phone,
                inquiry_id=inquiry_id,
                workflow_state=WorkflowState.AWAITING_CONFIRM,
            )
            db.add(session)

        if not _validate_transition(session.workflow_state, WorkflowState.ENTERING_PRODUCTS):
            raise WorkflowError(f"Cannot start workflow from {session.workflow_state}")

        session.workflow_state = WorkflowState.ENTERING_PRODUCTS
        inquiry.status = "confirmed"

        _record_event(
            db,
            tenant_id,
            EventType.INQUIRY_CONFIRMED,
            ActorType.SELLER,
            inquiry_id,
            session_id=session.id,
            payload={"seller_phone": seller_phone},
        )

        db.commit()

        return {
            "status": "ok",
            "session_id": session.id,
            "workflow_state": session.workflow_state.value,
            "message": "Order workflow started. Enter products: Name Qty Price (e.g. Juice 2 800)",
        }

    except Exception:
        db.rollback()
        raise


# ---------------------------------------------------------
# ADD PRODUCT
# ---------------------------------------------------------
def add_product(session_id: str, product_data: Dict[str, Any], db: Session) -> Dict[str, Any]:

    session = db.query(WorkflowSession).filter_by(id=session_id).first()
    if not session:
        raise WorkflowError(f"Session not found: {session_id}")

    if session.workflow_state != WorkflowState.ENTERING_PRODUCTS:
        raise WorkflowError(f"Cannot add product in state {session.workflow_state}")

    if session_id not in _products_cache:
        _products_cache[session_id] = []

    _products_cache[session_id].append(product_data)

    products = _products_cache[session_id]
    total = sum(p["quantity"] * p["price"] for p in products)

    return {
        "status": "ok",
        "action": "product_added",
        "product": product_data,
        "products_count": len(products),
        "running_total": total,
    }


# ---------------------------------------------------------
# GENERATE ORDER SUMMARY
# ---------------------------------------------------------
def generate_summary(session_id: str, db: Session) -> Dict[str, Any]:

    session = db.query(WorkflowSession).filter_by(id=session_id).first()
    if not session:
        raise WorkflowError("Session not found")

    if session.workflow_state != WorkflowState.ENTERING_PRODUCTS:
        raise WorkflowError("Invalid workflow state")

    products = _products_cache.get(session_id, [])
    if not products:
        raise WorkflowError("No products added")

    inquiry = session.inquiry
    tenant_id = inquiry.tenant_id if inquiry else None

    total = sum(p["quantity"] * p["price"] for p in products)

    try:

        order = Order(
            id=f"O{uuid.uuid4().hex[:8].upper()}",
            tenant_id=tenant_id,
            contact_id=inquiry.contact_id if inquiry else None,
            inquiry_id=session.inquiry_id,
            amount=total,
            customer_name=inquiry.message if inquiry else None,
            customer_phone=inquiry.contact.phone_number if inquiry and inquiry.contact else None,
            status="pending",
        )

        db.add(order)

        for p in products:
            db.add(
                OrderLineItem(
                    id=f"LI{uuid.uuid4().hex[:8].upper()}",
                    order_id=order.id,
                    product_name=p["product_name"],
                    quantity=p["quantity"],
                    unit_price=p["price"],
                    total_price=p["quantity"] * p["price"],
                )
            )

        session.order_id = order.id

        if not _validate_transition(session.workflow_state, WorkflowState.ORDER_SUMMARY):
            raise WorkflowError("Invalid transition")

        session.workflow_state = WorkflowState.ORDER_SUMMARY

        if tenant_id:
            _record_event(
                db,
                tenant_id,
                EventType.ORDER_CREATED,
                ActorType.SELLER,
                session.inquiry_id,
                order_id=order.id,
                session_id=session.id,
                payload={"products": products, "total": total},
            )

        db.commit()

    except Exception:
        db.rollback()
        raise

    summary_lines = ["Order Summary:"]
    for p in products:
        summary_lines.append(
            f"{p['product_name']} — {p['quantity']} × {p['price']} = {p['quantity']*p['price']} RWF"
        )

    summary_lines.append(f"TOTAL = {total} RWF")

    return {
        "status": "ok",
        "action": "order_summary",
        "order_id": order.id,
        "total": total,
        "products": products,
        "message": "\n".join(summary_lines),
    }


# ---------------------------------------------------------
# CONFIRM ORDER
# ---------------------------------------------------------
def confirm_order(session_id: str, db: Session) -> Dict[str, Any]:

    session = db.query(WorkflowSession).filter_by(id=session_id).first()
    if not session:
        raise WorkflowError("Session not found")

    if session.workflow_state != WorkflowState.ORDER_SUMMARY:
        raise WorkflowError("Invalid workflow state")

    inquiry = session.inquiry
    tenant_id = inquiry.tenant_id if inquiry else None

    try:

        if not _validate_transition(session.workflow_state, WorkflowState.AWAITING_PAYMENT):
            raise WorkflowError("Invalid transition")

        session.workflow_state = WorkflowState.AWAITING_PAYMENT

        if tenant_id:
            _record_event(
                db,
                tenant_id,
                EventType.ORDER_CONFIRMED,
                ActorType.SELLER,
                session.inquiry_id,
                order_id=session.order_id,
                session_id=session.id,
            )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "status": "ok",
        "action": "order_confirmed",
        "workflow_state": session.workflow_state.value,
        "message": "Order confirmed. Ask customer to pay. When paid type PAID.",
    }


# ---------------------------------------------------------
# RECORD PAYMENT
# ---------------------------------------------------------
def record_payment(session_id: str, db: Session) -> Dict[str, Any]:

    session = db.query(WorkflowSession).filter_by(id=session_id).first()
    if not session:
        raise WorkflowError("Session not found")

    if session.workflow_state != WorkflowState.AWAITING_PAYMENT:
        raise WorkflowError("Invalid workflow state")

    inquiry = session.inquiry
    tenant_id = inquiry.tenant_id if inquiry else None

    try:

        session.workflow_state = WorkflowState.COMPLETED

        if session.order:
            session.order.status = "paid"

        if tenant_id:
            _record_event(
                db,
                tenant_id,
                EventType.PAYMENT_RECORDED,
                ActorType.SELLER,
                session.inquiry_id,
                order_id=session.order_id,
                session_id=session.id,
            )

        db.commit()

    except Exception:
        db.rollback()
        raise

    clear_session_products(session_id)

    return {
        "status": "ok",
        "action": "payment_recorded",
        "workflow_state": session.workflow_state.value,
        "message": "Payment recorded. Order completed.",
    }


# ---------------------------------------------------------
# CANCEL WORKFLOW
# ---------------------------------------------------------
def cancel_workflow(session_id: str, db: Session) -> Dict[str, Any]:

    session = db.query(WorkflowSession).filter_by(id=session_id).first()
    if not session:
        raise WorkflowError("Session not found")

    inquiry = session.inquiry
    tenant_id = inquiry.tenant_id if inquiry else None

    try:

        if _validate_transition(session.workflow_state, WorkflowState.CANCELLED):
            session.workflow_state = WorkflowState.CANCELLED

            if tenant_id:
                _record_event(
                    db,
                    tenant_id,
                    EventType.INQUIRY_DROPPED,
                    ActorType.SELLER,
                    session.inquiry_id,
                    session_id=session.id,
                )

        db.commit()

    except Exception:
        db.rollback()
        raise

    clear_session_products(session_id)

    return {
        "status": "ok",
        "action": "workflow_cancelled",
        "workflow_state": session.workflow_state.value,
        "message": "Order cancelled. Type CONFIRM to start again.",
    }


# ---------------------------------------------------------
# CACHE HELPERS
# ---------------------------------------------------------
def get_session_products(session_id: str) -> List[Dict[str, Any]]:
    return _products_cache.get(session_id, [])


def clear_session_products(session_id: str) -> None:
    if session_id in _products_cache:
        del _products_cache[session_id]