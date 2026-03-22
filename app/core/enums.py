# Shared enums (statuses, payment modes)

from enum import Enum


class ActorType(str, Enum):
    SELLER = "seller"
    SYSTEM = "system"
    CUSTOMER = "customer"


class EventType(str, Enum):
    INBOUND_MESSAGE = "inbound_message"
    OUTBOUND_MESSAGE = "outbound_message"
    SALE_STARTED = "sale_started"
    PRODUCT_ADDED = "product_added"
    SALE_COMPLETED = "sale_completed"
    SUMMARY_REQUESTED = "summary_requested"
    SYSTEM_ERROR = "system_error"
    OPT_OUT = "opt_out"
    BLOCKED_SEND = "blocked_send"
    FAILED_SEND = "failed_send"
    QUALITY_WARNING = "quality_warning"
    PAYMENT_RECORDED = "payment_recorded"
    ORDER_CREATED = "order_created"
    INQUIRY_DROPPED = "inquiry_dropped"
    ORDER_CREATION_FAILED = "order_creation_failed"
    INQUIRY_CONFIRMED = "inquiry_confirmed"
    INQUIRY_CREATED = "inquiry_created"


class CoexistenceStatus(str, Enum):
    """Represents seller coexistence onboarding states."""
    PENDING = "pending"      # Just onboarded, not verified yet
    ACTIVE = "active"        # Approved and allowed to send messages
    BLOCKED = "blocked"      # Explicitly prohibited
    SUSPENDED = "suspended"  # Temporary restriction for policy violation


class WorkflowState(str, Enum):
    """Represents workflow session states in the payment workflow."""
    IDLE = "idle"                         # Default state, no active transaction
    AWAITING_CONFIRM = "awaiting_confirm" # Waiting for seller to confirm inquiry
    ENTERING_PRODUCTS = "entering_products" # Seller entering product details
    ORDER_SUMMARY = "order_summary"       # Showing order summary to seller
    AWAITING_PAYMENT = "awaiting_payment" # Waiting for payment confirmation
    CANCELLED = "cancelled"               # Workflow cancelled by seller
    WAITING_PRODUCT = "waiting_product"   # Waiting for product name input
    WAITING_QUANTITY = "waiting_quantity" # Waiting for quantity input
    WAITING_AMOUNT = "waiting_amount"     # Waiting for total amount input
    WAITING_ADD_MORE = "waiting_add_more" # Waiting for YES/NO to add another product
    COMPLETED = "completed"               # Transaction completed, payment recorded

    #------New single-line product input -----------
    WAITING_PRODUCT_LINE = "waiting_product_line" # Waiting for "<product> <quantity> <unit price>" input
