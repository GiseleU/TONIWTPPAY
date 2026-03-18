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
from app.core.enums import WorkflowState
from app.db.session import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])


# --------------------------
# Start Transaction
# --------------------------
@router.post("/start", response_model=StartTransactionResponse)
def start_transaction(request: StartTransactionRequest, db: Session = Depends(get_db)):
    state = get_or_create_state(db, request.seller_phone, request.tenant_id)

    tx = create_transaction(db, request.seller_phone, request.tenant_id)

    state.state = WorkflowState.WAITING_PRODUCT.value
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
    try:
        item = add_item(
            db,
            transaction_id=request.transaction_id,
            tenant_id=request.tenant_id,
            product_name=request.product_name,
            quantity=request.quantity,
            total_amount=request.total_amount
        )

        return AddItemResponse(
            item_id=item.id,
            product_name=item.product_name,
            quantity=item.quantity,
            total_amount=item.total_amount
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --------------------------
# Finalize Transaction
# --------------------------
@router.post("/finalize", response_model=FinalizeTransactionResponse)
def finalize_transaction(request: FinalizeTransactionRequest, db: Session = Depends(get_db)):
    """
    TEMP implementation until finalize_transaction_service is created.
    """

    state = get_or_create_state(db, request.seller_phone, request.tenant_id)

    if not state.current_transaction_id:
        raise HTTPException(status_code=400, detail="No active transaction")

    # Fetch items
    from app.models.transaction_item import TransactionItem

    items = db.query(TransactionItem).filter(
        TransactionItem.transaction_id == request.transaction_id
    ).all()

    if not items:
        raise HTTPException(status_code=400, detail="No items in transaction")

    # Build summary
    total = sum(item.total_amount for item in items)

    summary_lines = [
        f"{item.product_name} x{item.quantity} = {item.total_amount}"
        for item in items
    ]

    summary_text = "\n".join(summary_lines)
    summary_text += f"\n\nTotal: {total}"

    # Reset state
    reset_state(state, db=db)

    return FinalizeTransactionResponse(summary=summary_text)