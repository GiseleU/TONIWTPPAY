# app/routers/transactions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.transaction import (
    StartTransactionRequest,
    StartTransactionResponse,
    AddItemRequest,
    AddItemResponse,
    FinalizeTransactionRequest,
    FinalizeTransactionResponse
)

from app.services.transaction_service import create_transaction, add_item
from app.services.state_service import get_or_create_state, reset_state
from app.services.whatsapp_service import finalize_transaction as finalize_tx
from app.core.enums import WorkflowState
from app.db.session import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])


# --------------------------
# Start Transaction
# --------------------------
@router.post("/start", response_model=StartTransactionResponse)
def start_transaction(request: StartTransactionRequest, db: Session = Depends(get_db)):
    """
    Start a new transaction for a seller.
    """
    state = get_or_create_state(db, request.seller_phone, request.tenant_id)
    tx = create_transaction(db, request.seller_phone, request.tenant_id)

    # Use WAITING_PRODUCT_LINE to match WhatsApp workflow
    state.state = WorkflowState.WAITING_PRODUCT_LINE.value
    state.current_transaction_id = tx.id

    db.commit()
    db.refresh(state)

    return StartTransactionResponse(
        transaction_id=tx.id,
        state=state.state
    )


# --------------------------
# Add Item
# --------------------------
@router.post("/add_item", response_model=AddItemResponse)
def add_item_to_transaction(request: AddItemRequest, db: Session = Depends(get_db)):
    """
    Add a product item to an existing transaction.
    """
    try:
        item = add_item(
            db,
            transaction_id=request.transaction_id,
            tenant_id=request.tenant_id,
            product_name=request.product_name,
            quantity=request.quantity,
            unit_price=request.unit_price
        )

        return AddItemResponse(
            item_id=item.id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=float(item.unit_price),  # Convert Decimal back to float for response
            total_amount=float(item.total_amount)
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --------------------------
# Finalize Transaction
# --------------------------
@router.post("/finalize", response_model=FinalizeTransactionResponse)
def finalize_transaction_endpoint(request: FinalizeTransactionRequest, db: Session = Depends(get_db)):
    """
    Finalize an active transaction: generate a summary and reset state.
    """
    state = get_or_create_state(db, request.seller_phone, request.tenant_id)

    if not state.current_transaction_id:
        raise HTTPException(status_code=400, detail="No active transaction")

    # Use shared WhatsApp service function for consistent summary
    summary_text = finalize_tx(db, state)

    db.commit()
    return FinalizeTransactionResponse(summary=summary_text)