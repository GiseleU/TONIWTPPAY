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
    INQUIRY_DROPPED = "inquiry_dropped"
    ORDER_CREATED = "order_created"
    PAYMENT_MARKED = "payment_marked"
    SYSTEM_ERROR = "system_error"


class CoexistenceStatus(str, Enum):
    """Represents seller coexistence onboarding states."""
    PENDING = "pending"      # Just onboarded, not verified yet
    ACTIVE = "active"        # Approved and allowed to send messages
    BLOCKED = "blocked"      # Explicitly prohibited
    SUSPENDED = "suspended"  # Temporary restriction for policy violation