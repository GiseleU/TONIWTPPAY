# app/services/seller_command_service.py
from sqlalchemy.orm import Session
from app.models.inquiry import Inquiry
from app.models.event import Event
from app.models.tenant import Tenant
from app.models.workflow_session import WorkflowSession
from app.core.enums import EventType, ActorType, WorkflowState
from app.services.summary_service import generate_daily_summary
from app.core.datetime_utils import get_today
import uuid
import re
from typing import Optional, Dict, Any, List

# Allowed transitions for inquiries
INQUIRY_TRANSITIONS = {
    "new": ["confirmed", "dropped"],
    "confirmed": ["completed", "dropped"],
    "dropped": [],
    "completed": [],
}

# Allowed workflow state transitions
WORKFLOW_TRANSITIONS = {
    WorkflowState.AWAITING_CONFIRM: [WorkflowState.ENTERING_PRODUCTS, WorkflowState.CANCELLED],
    WorkflowState.ENTERING_PRODUCTS: [WorkflowState.ORDER_SUMMARY, WorkflowState.CANCELLED],
    WorkflowState.ORDER_SUMMARY: [WorkflowState.AWAITING_PAYMENT, WorkflowState.ENTERING_PRODUCTS, WorkflowState.CANCELLED],
    WorkflowState.AWAITING_PAYMENT: [WorkflowState.COMPLETED, WorkflowState.CANCELLED],
    WorkflowState.COMPLETED: [],
    WorkflowState.CANCELLED: [WorkflowState.AWAITING_CONFIRM],
}


class CommandError(Exception):
    """Raised when a seller command is invalid or cannot be executed."""
    pass


class WorkflowError(Exception):
    """Raised when workflow state transition is invalid."""
    pass


# In-memory storage for products being entered (temporary, will be replaced with database in Phase 3)
# Key: session_id, Value: List of {"product_name": str, "quantity": int, "price": int}
_products_cache: Dict[str, List[Dict[str, Any]]] = {}


def parse_seller_command(command_text: str):
    """
    Parses seller commands (simplified - no IDs required):
    - CONFIRM - Start workflow on latest "new" inquiry
    - PAID - Record payment on active workflow session
    - YES - Confirm order summary
    - NO - Restart/cancel workflow
    - DONE - Finish product entry
    - SUMMARY - Get daily summary (unchanged)
    - [Product Entry] - e.g., "Juice 2 800"
    
    Returns dict with action and optional parameters
    """
    command_text = command_text.strip().upper()

    # CONFIRM - Start workflow
    if command_text == "CONFIRM":
        return {"action": "confirm"}

    # PAID - Record payment
    if command_text == "PAID":
        return {"action": "paid"}

    # YES - Confirm order summary
    if command_text == "YES" or command_text == "YEGO":
        return {"action": "yes"}

    # NO - Restart/cancel
    if command_text == "NO" or command_text == "OYA":
        return {"action": "no"}

    # DONE - Finish product entry
    if command_text == "DONE":
        return {"action": "done"}

    # SUMMARY - Daily summary (unchanged)
    if command_text == "SUMMARY":
        return {"action": "summary"}

    # Product entry pattern: "Product Name Quantity Price"
    # Example: "Juice 2 800" or "Soda 1 600"
    product_match = re.match(r"^(.+?)\s+(\d+)\s+(\d+)$", command_text)
    if product_match:
        return {
            "action": "add_product",
            "product_name": product_match.group(1).strip(),
            "quantity": int(product_match.group(2)),
            "price": int(product_match.group(3))
        }

    raise CommandError(f"Invalid command format: {command_text}")


def get_active_workflow_session(seller_phone: str, tenant_id: str, db: Session) -> Optional[WorkflowSession]:
    """
    Get the active workflow session for a seller.
    Returns the most recent active session (not completed/cancelled).
    """
    return db.query(WorkflowSession).filter(
        WorkflowSession.seller_phone == seller_phone,
        WorkflowSession.inquiry_id.in_(
            db.query(Inquiry.id).filter(Inquiry.tenant_id == tenant_id)
        ),
        WorkflowSession.workflow_state.in_([
            WorkflowState.AWAITING_CONFIRM,
            WorkflowState.ENTERING_PRODUCTS,
            WorkflowState.ORDER_SUMMARY,
            WorkflowState.AWAITING_PAYMENT,
        ])
    ).order_by(WorkflowSession.created_at.desc()).first()


def get_latest_new_inquiry(seller_phone: str, tenant_id: str, db: Session) -> Optional[Inquiry]:
    """
    Get the latest "new" inquiry for a seller.
    This is used when seller types CONFIRM without specifying an inquiry ID.
    """
    # Get all inquiries for this tenant
    # Then find the one with most recent created_at where status is "new"
    return db.query(Inquiry).filter(
        Inquiry.tenant_id == tenant_id,
        Inquiry.status == "new"
    ).order_by(Inquiry.created_at.desc()).first()


def validate_workflow_transition(current_state: WorkflowState, new_state: WorkflowState) -> bool:
    """Validate if workflow state transition is allowed."""
    allowed_states = WORKFLOW_TRANSITIONS.get(current_state, [])
    return new_state in allowed_states


def execute_seller_command(command_text: str, seller_id: str, tenant_id: str, db: Session, seller_phone: str = None):
    """
    Executes a seller command (simplified workflow):
    - CONFIRM - Start workflow on latest "new" inquiry
    - PAID - Record payment on active workflow session
    - YES/NO - Confirm/reject order summary
    - DONE - Finish product entry
    - add_product - Add product to current session
    - SUMMARY - Get daily summary (unchanged)
    
    Args:
        command_text: The command text from seller
        seller_id: Seller ID for authorization
        tenant_id: Tenant ID
        db: Database session
        seller_phone: Seller's phone number (for session tracking)
    """
    # Parse command
    command = parse_seller_command(command_text)

    # --- SUMMARY command (unchanged) ---
    if command["action"] == "summary":
        summary_date = get_today()
        summary = generate_daily_summary(db, tenant_id, summary_date)
        return {
            "status": "ok",
            "summary": {
                "total_orders": summary.total_orders,
                "total_revenue": float(summary.total_revenue),
                "paid_orders": summary.paid_orders,
                "paid_revenue": float(summary.paid_revenue),
                "total_inquiries": summary.total_inquiries,
                "confirmed_inquiries": summary.confirmed_inquiries,
                "dropped_inquiries": summary.dropped_inquiries,
                "opt_outs": summary.opt_outs,
                "blocked_sends": summary.blocked_sends,
                "failed_sends": summary.failed_sends,
                "quality_warnings": summary.quality_warnings,
            }
        }

    # --- CONFIRM command (new simplified workflow) ---
    if command["action"] == "confirm":
        # Find the latest "new" inquiry for this tenant
        inquiry = get_latest_new_inquiry(seller_phone or seller_id, tenant_id, db)
        if not inquiry:
            raise CommandError("No pending inquiry found. Customer must send a message first.")
        
        # Check if workflow session already exists
        existing_session = get_active_workflow_session(seller_phone or seller_id, tenant_id, db)
        if existing_session:
            # Resume existing session
            session = existing_session
        else:
            # Create new workflow session
            session = WorkflowSession(
                id=WorkflowSession.generate_id(),
                seller_phone=seller_phone or seller_id,
                inquiry_id=inquiry.id,
                workflow_state=WorkflowState.AWAITING_CONFIRM,
            )
            db.add(session)
        
        # Transition to ENTERING_PRODUCTS
        if validate_workflow_transition(session.workflow_state, WorkflowState.ENTERING_PRODUCTS):
            session.workflow_state = WorkflowState.ENTERING_PRODUCTS
            inquiry.status = "confirmed"
            
            # Record event
            event = Event(
                id=str(uuid.uuid4()),
                event_type=EventType.INQUIRY_CONFIRMED,
                actor=ActorType.SELLER,
                tenant_id=tenant_id,
                inquiry_id=inquiry.id,
                payload={"command": command_text, "seller_phone": seller_phone}
            )
            db.add(event)
            db.commit()
            
            return {
                "status": "ok",
                "action": "workflow_started",
                "inquiry_id": inquiry.id,
                "session_id": session.id,
                "message": "Order workflow started. Please enter products: Product Name Quantity Price (e.g., Juice 2 800)"
            }
        else:
            raise WorkflowError(f"Cannot start workflow from state: {session.workflow_state}")

    # --- PAID command (new simplified workflow) ---
    if command["action"] == "paid":
        # Find active workflow session
        session = get_active_workflow_session(seller_phone or seller_id, tenant_id, db)
        if not session:
            raise CommandError("No active order found. Type CONFIRM to start a new order.")
        
        if session.workflow_state != WorkflowState.AWAITING_PAYMENT:
            raise CommandError(f"Cannot record payment in current state: {session.workflow_state}. Please complete order confirmation first.")
        
        # Transition to COMPLETED
        if validate_workflow_transition(session.workflow_state, WorkflowState.COMPLETED):
            session.workflow_state = WorkflowState.COMPLETED
            
            # Update order status
            if session.order:
                session.order.status = "paid"
            
            # Record event
            event = Event(
                id=str(uuid.uuid4()),
                event_type=EventType.PAYMENT_RECORDED,
                actor=ActorType.SELLER,
                tenant_id=tenant_id,
                inquiry_id=session.inquiry_id,
                order_id=session.order_id,
                payload={"command": command_text, "seller_phone": seller_phone}
            )
            db.add(event)
            db.commit()
            
            return {
                "status": "ok",
                "action": "payment_recorded",
                "session_id": session.id,
                "message": "Payment recorded! Order is complete. Thank you!"
            }
        else:
            raise WorkflowError(f"Cannot complete payment from state: {session.workflow_state}")

    # --- YES command (confirm order summary) ---
    if command["action"] == "yes":
        session = get_active_workflow_session(seller_phone or seller_id, tenant_id, db)
        if not session:
            raise CommandError("No active order found. Type CONFIRM to start a new order.")
        
        if session.workflow_state != WorkflowState.ORDER_SUMMARY:
            raise CommandError(f"Cannot confirm in current state: {session.workflow_state}")
        
        # Transition to AWAITING_PAYMENT
        if validate_workflow_transition(session.workflow_state, WorkflowState.AWAITING_PAYMENT):
            session.workflow_state = WorkflowState.AWAITING_PAYMENT
            
            # Record event
            event = Event(
                id=str(uuid.uuid4()),
                event_type=EventType.ORDER_CREATED,
                actor=ActorType.SELLER,
                tenant_id=tenant_id,
                inquiry_id=session.inquiry_id,
                order_id=session.order_id,
                payload={"command": command_text, "seller_phone": seller_phone}
            )
            db.add(event)
            db.commit()
            
            return {
                "status": "ok",
                "action": "order_confirmed",
                "session_id": session.id,
                "message": "Order confirmed! Ask customer to pay. When payment is received, type PAID."
            }
        else:
            raise WorkflowError(f"Cannot confirm order from state: {session.workflow_state}")

    # --- NO command (restart/cancel workflow) ---
    if command["action"] == "no":
        session = get_active_workflow_session(seller_phone or seller_id, tenant_id, db)
        if session:
            # Cancel current session
            session.workflow_state = WorkflowState.CANCELLED
            
            # Record event
            event = Event(
                id=str(uuid.uuid4()),
                event_type=EventType.INQUIRY_DROPPED,
                actor=ActorType.SELLER,
                tenant_id=tenant_id,
                inquiry_id=session.inquiry_id,
                payload={"command": command_text, "seller_phone": seller_phone}
            )
            db.add(event)
            db.commit()
        
        # Clear products cache
        if session and session.id in _products_cache:
            del _products_cache[session.id]
        
        return {
            "status": "ok",
            "action": "workflow_cancelled",
            "message": "Order cancelled. Type CONFIRM to start a new order."
        }

    # --- DONE command (finish product entry) ---
    if command["action"] == "done":
        session = get_active_workflow_session(seller_phone or seller_id, tenant_id, db)
        if not session:
            raise CommandError("No active order found. Type CONFIRM to start a new order.")
        
        if session.workflow_state != WorkflowState.ENTERING_PRODUCTS:
            raise CommandError(f"Cannot finish product entry in current state: {session.workflow_state}")
        
        # Get products from cache
        products = _products_cache.get(session.id, [])
        if not products:
            raise CommandError("No products entered. Please add at least one product.")
        
        # Calculate total
        total = sum(p["quantity"] * p["price"] for p in products)
        
        # Transition to ORDER_SUMMARY
        if validate_workflow_transition(session.workflow_state, WorkflowState.ORDER_SUMMARY):
            session.workflow_state = WorkflowState.ORDER_SUMMARY
            
            # Generate summary message
            summary_lines = ["Order Summary:"]
            for p in products:
                line_total = p["quantity"] * p["price"]
                summary_lines.append(f"{p['product_name']} — {p['quantity']} × {p['price']} = {line_total} RWF")
            summary_lines.append(f"TOTAL = {total} RWF")
            summary_lines.append("")
            summary_lines.append("Ese ibi ni byo?")
            
            db.commit()
            
            return {
                "status": "ok",
                "action": "order_summary",
                "session_id": session.id,
                "products": products,
                "total": total,
                "message": "\n".join(summary_lines)
            }
        else:
            raise WorkflowError(f"Cannot finish product entry from state: {session.workflow_state}")

    # --- add_product command ---
    if command["action"] == "add_product":
        session = get_active_workflow_session(seller_phone or seller_id, tenant_id, db)
        if not session:
            raise CommandError("No active order found. Type CONFIRM to start a new order.")
        
        if session.workflow_state != WorkflowState.ENTERING_PRODUCTS:
            raise CommandError(f"Cannot add products in current state: {session.workflow_state}. Type DONE to finish product entry.")
        
        # Add product to cache
        if session.id not in _products_cache:
            _products_cache[session.id] = []
        
        product_data = {
            "product_name": command["product_name"],
            "quantity": command["quantity"],
            "price": command["price"]
        }
        _products_cache[session.id].append(product_data)
        
        # Calculate running total
        products = _products_cache[session.id]
        total = sum(p["quantity"] * p["price"] for p in products)
        
        return {
            "status": "ok",
            "action": "product_added",
            "session_id": session.id,
            "product": product_data,
            "products_count": len(products),
            "running_total": total,
            "message": f"{command['product_name']} added! (Qty: {command['quantity']}, Price: {command['price']})\nHari ikindi gicuruzwa? (Type another product or DONE to finish)"
        }

    raise CommandError(f"Unknown action: {command['action']}")
