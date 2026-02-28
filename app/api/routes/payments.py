# app/api/routes/payments.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.services.payment_service import record_manual_payment, PaymentError
from app.models.payment import Payment
from app.schemas.payment import PaymentCreateRequest, PaymentResponse

router = APIRouter()

@router.post("/payments", response_model=PaymentResponse)
def record_payment(
    request: PaymentCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Record a manual payment for an order.
    """
    try:
        payment = record_manual_payment(
            order_id=request.order_id,
            amount=request.amount,
            verified_by=request.verified_by,
            method=request.method,
            notes=request.notes,
            db=db,
        )
        return PaymentResponse.from_orm(payment)
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
):
    """
    Fetch a specific payment by ID.
    """
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentResponse.from_orm(payment)

@router.get("/payments", response_model=List[PaymentResponse])
def list_payments(
    order_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List payments, optionally filtered by order_id or tenant_id.
    """
    query = db.query(Payment)
    if order_id:
        query = query.filter(Payment.order_id == order_id)
    if tenant_id:
        query = query.filter(Payment.tenant_id == tenant_id)
    payments = query.all()
    return [PaymentResponse.from_orm(p) for p in payments]
