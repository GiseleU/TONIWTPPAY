from sqlalchemy.orm import Session
from app.models.inquiry import Inquiry
from app.models.contact import Contact
from app.models.tenant import Tenant
from app.models.event import Event
from app.core.enums import CoexistenceStatus, EventType, ActorType
from app.services.notification_service import get_notification_service
import uuid


def handle_whatsapp_message(payload: dict, db: Session) -> dict:
    """
    Handles inbound WhatsApp messages:
    - Checks idempotency
    - Validates tenant coexistence status
    - Finds or creates contact
    - Creates inquiry
    - Records event
    """
    idempotency_key = payload.get("message_id")

    # 1️⃣ Avoid duplicate inquiries
    existing_inquiry = db.query(Inquiry).filter_by(idempotency_key=idempotency_key).first()
    if existing_inquiry:
        return {"status": "duplicate", "inquiry_id": existing_inquiry.id}

    # 2️⃣ Find tenant by WA number
    tenant = db.query(Tenant).join(Tenant.whatsapp_accounts).filter(
        Tenant.whatsapp_accounts.any(phone_number=payload.get("to"))
    ).first()
    if not tenant:
        raise ValueError("Tenant not found")

    # 3️⃣ Check coexistence status
    if tenant.coexistence_status != CoexistenceStatus.ACTIVE:
        raise PermissionError("Tenant not active for inbound messages")

    # 4️⃣ Find or create contact
    contact_phone = payload.get("from")
    contact = db.query(Contact).filter_by(phone_number=contact_phone, tenant_id=tenant.id).first()
    if not contact:
        contact = Contact(
            id=str(uuid.uuid4()),
            phone_number=contact_phone,
            tenant_id=tenant.id,
            name=contact_phone
        )
        db.add(contact)
        db.flush()

    # 5️⃣ Select WhatsApp account
    whatsapp_account = next(
        (wa for wa in tenant.whatsapp_accounts if wa.phone_number == payload.get("to")),
        tenant.whatsapp_accounts[0]
    )

    # 6️⃣ Create Inquiry
    inquiry = Inquiry(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        contact_id=contact.id,
        whatsapp_account_id=whatsapp_account.id,
        message=payload.get("text"),
        idempotency_key=idempotency_key,
        status="new"
    )
    db.add(inquiry)
    db.flush()

    # 7️⃣ Record Event
    event = Event(
        id=str(uuid.uuid4()),
        event_type=EventType.INQUIRY_CREATED,
        actor=ActorType.CUSTOMER,
        tenant_id=tenant.id,
        contact_id=contact.id,
        inquiry_id=inquiry.id,
        payload=payload
    )
    db.add(event)
    db.commit()

    return {"status": "ok", "inquiry_id": inquiry.id}


async def send_inquiry_reminder(
    inquiry_id: str,
    tenant_id: str,
    db: Session,
    whatsapp_account_id: str = None
) -> dict:
    """
    Optionally send a reminder to the seller after creating an inquiry.
    
    Args:
        inquiry_id: The created inquiry ID
        tenant_id: Tenant ID
        db: Database session
        whatsapp_account_id: WhatsApp account ID for sending the reminder
        
    Returns:
        Dict with reminder send status
    """
    # Get the inquiry to find the seller's phone
    inquiry = db.query(Inquiry).filter_by(id=inquiry_id).first()
    if not inquiry:
        return {"status": "error", "message": "Inquiry not found"}
    
    # Get tenant to find the seller's phone number
    tenant = db.query(Tenant).filter_by(id=tenant_id).first()
    if not tenant:
        return {"status": "error", "message": "Tenant not found"}
    
    # Find the WhatsApp account to use
    whatsapp_account = None
    if whatsapp_account_id:
        from app.models.whatsapp_account import WhatsAppAccount
        whatsapp_account = db.query(WhatsAppAccount).filter_by(id=whatsapp_account_id).first()
    
    if not whatsapp_account and tenant.whatsapp_accounts:
        whatsapp_account = tenant.whatsapp_accounts[0]
    
    if not whatsapp_account:
        return {"status": "error", "message": "WhatsApp account not found"}
    
    # Send the reminder message to seller
    reminder_message = "Ufite inquiry nshya. Andika CONFIRM gutangira order."
    
    try:
        notification_service = get_notification_service()
        result = await notification_service.send_message(
            to_phone=tenant.phone_number,  # Seller's phone number
            message=reminder_message,
            tenant_id=tenant_id,
            whatsapp_account_id=whatsapp_account.id,
            message_type="inquiry_reminder",
            related_inquiry_id=inquiry_id,
            db=db
        )
        return {"status": "ok", "reminder_sent": True, "result": result}
    except Exception as e:
        return {"status": "error", "reminder_sent": False, "error": str(e)}


def handle_momo_webhook(payload: dict, db: Session) -> dict:
    """
    Handles inbound MoMo payment notifications:
    - Checks idempotency using transaction ID
    - Finds tenant by MoMo account (simplified)
    - Records payment event
    """
    transaction_id = payload.get("transaction_id")
    if not transaction_id:
        raise ValueError("Transaction ID missing")

    # Avoid duplicate processing
    existing_event = db.query(Event).filter_by(idempotency_key=transaction_id).first()
    if existing_event:
        return {"status": "duplicate", "event_id": existing_event.id}

    # 1️⃣ Find tenant
    tenant = db.query(Tenant).filter_by(id=payload.get("tenant_id")).first()
    if not tenant:
        raise ValueError("Tenant not found")

    # 2️⃣ Check coexistence status
    if tenant.coexistence_status != CoexistenceStatus.ACTIVE:
        raise PermissionError("Tenant not active for MoMo transactions")

    # 3️⃣ Record payment event
    event = Event(
        id=str(uuid.uuid4()),
        event_type=EventType.PAYMENT_RECORDED,
        actor=ActorType.SYSTEM,
        tenant_id=tenant.id,
        payload=payload,
        idempotency_key=transaction_id
    )
    db.add(event)
    db.commit()

    return {"status": "ok", "event_id": event.id}
