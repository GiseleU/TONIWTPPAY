# app/services/state_service.py
from sqlalchemy.orm import Session
from app.models.conversation_state import ConversationState
from app.core.enums import WorkflowState
import uuid


def get_or_create_state(db: Session, seller_phone: str, tenant_id: str) -> ConversationState:
    """
    Retrieve an existing ConversationState for a seller, or create one if it doesn't exist.
    """
    state = (
        db.query(ConversationState)
        .filter_by(tenant_id=tenant_id, seller_phone=seller_phone)
        .first()
    )

    if not state:
        state = ConversationState(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            seller_phone=seller_phone,
            state=WorkflowState.IDLE.value,
        )
        db.add(state)
        db.commit()
        db.refresh(state)

    return state


def reset_state(state: ConversationState, db: Session = None):
    """
    Reset a ConversationState to its initial idle state.
    If `db` is provided, changes will be committed immediately.
    """
    state.state = WorkflowState.IDLE.value
    state.current_transaction_id = None
    state.temp_product_name = None
    state.temp_quantity = None
    state.temp_unit_price = None

    if db:
        db.commit()
        db.refresh(state)