# app/api/routes/orders.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from app.db.session import get_db
from app.models.order import Order
from app.models.event import Event
from app.core.enums import EventType, ActorType
from app.services.order_state_service import create_order_from_inquiry, OrderStateError
from app.core.policy_guard import PolicyGuard
from app.schemas.order import CreateOrderRequest, OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


# -----------------------------
# POST /orders/from-inquiry
# -----------------------------
@router.post("/from-inquiry", response_model=OrderResponse)
def create_order_endpoint(request: CreateOrderRequest, db: Session = Depends(get_db)):
    """
    Create an order from a confirmed inquiry.
    Logs ORDER_CREATED or ORDER_CREATION_FAILED events.
    """
    try:
        order = create_order_from_inquiry(
            inquiry_id=request.inquiry_id,
            tenant_id=request.tenant_id,
            customer_name=request.customer_name,
            customer_phone=request.customer_phone,
            customer_address=request.customer_address,
            db=db,
        )
    except OrderStateError as e:
        # Log failure event
        db.add(Event(
            id=str(uuid.uuid4()),
            event_type=EventType.ORDER_CREATION_FAILED,
            actor=ActorType.SYSTEM,
            tenant_id=request.tenant_id,
            inquiry_id=request.inquiry_id,
            payload={"detail": str(e)}
        ))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # PolicyGuard stub: outbound messages not sent yet
    if not PolicyGuard.can_send_message(order.tenant_id, order.id):
        # For now, just log / skip sending
        pass

    # Log success event
    db.add(Event(
        id=str(uuid.uuid4()),
        event_type=EventType.ORDER_CREATED,
        actor=ActorType.SYSTEM,
        tenant_id=order.tenant_id,
        inquiry_id=order.inquiry_id,
        order_id=order.id,
        payload={}
    ))
    db.commit()

    return OrderResponse(
        id=order.id,
        tenant_id=order.tenant_id,
        inquiry_id=order.inquiry_id,
        contact_id=order.contact_id,
        amount=order.amount,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        customer_address=order.customer_address,
        retention_tag=order.retention_tag,
    )


# -----------------------------
# GET /orders/{order_id}
# -----------------------------
@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, db: Session = Depends(get_db)):
    """
    Retrieve an order by ID
    """
    order = db.query(Order).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )

    return OrderResponse(
        id=order.id,
        tenant_id=order.tenant_id,
        inquiry_id=order.inquiry_id,
        contact_id=order.contact_id,
        amount=order.amount,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        customer_address=order.customer_address,
        retention_tag=order.retention_tag,
    )


# -----------------------------
# GET /orders?tenant_id=
# -----------------------------
@router.get("/", response_model=List[OrderResponse])
def list_orders(tenant_id: str, db: Session = Depends(get_db)):
    """
    List all orders for a given tenant.
    """
    orders = db.query(Order).filter_by(tenant_id=tenant_id).all()
    return [
        OrderResponse(
            id=o.id,
            tenant_id=o.tenant_id,
            inquiry_id=o.inquiry_id,
            contact_id=o.contact_id,
            amount=o.amount,
            customer_name=o.customer_name,
            customer_phone=o.customer_phone,
            customer_address=o.customer_address,
            retention_tag=o.retention_tag,
        )
        for o in orders
    ]