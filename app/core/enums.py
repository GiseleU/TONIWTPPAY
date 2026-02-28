# Shared enums (statuses, payment modes)

from enum import Enum


class ActorType(str, Enum):
    CUSTOMER = "customer"
    SELLER = "seller"
    SYSTEM = "system"


class EventType(str, Enum):
    INBOUND_MESSAGE = "inbound_message"
    OUTBOUND_MESSAGE = "outbound_message"
    INQUIRY_CREATED = "inquiry_created"
    INQUIRY_CONFIRMED = "inquiry_confirmed"
    INQUIRY_DROPPED = "inquiry_dropped"
    ORDER_CREATED = "order_created"
    ORDER_CREATION_FAILED = "order_creation_failed"
    PAYMENT_RECORDED = "payment_recorded"
    PAYMENT_FAILED = "payment_failed"
    SYSTEM_ERROR = "system_error"
    OPT_OUT = "opt_out"
    BLOCKED_SEND = "blocked_send"
    FAILED_SEND = "failed_send"
    QUALITY_WARNING = "quality_warning"


class CoexistenceStatus(str, Enum):
    """Represents seller coexistence onboarding states."""
    PENDING = "pending"      # Just onboarded, not verified yet
    ACTIVE = "active"        # Approved and allowed to send messages
    BLOCKED = "blocked"      # Explicitly prohibited
    SUSPENDED = "suspended"  # Temporary restriction for policy violation