from sqlalchemy.orm import Session
import uuid

from app.models.inquiry import Inquiry
from app.models.contact import Contact
from app.models.tenant import Tenant
from app.models.event import Event

from app.core.enums import CoexistenceStatus, EventType, ActorType


# =========================================================
# WhatsApp Webhook Handler
# =========================================================
def handle_whatsapp_message(payload: dict, db: Session) -> dict:
    """
    Process inbound WhatsApp message from webhook.

    Flow:
    1. Idempotency check
    2. Tenant lookup via WhatsApp phone_number_id
    3. Coexistence validation
    4. Contact lookup or creation
    5. WhatsApp account selection
    6. Inquiry creation
    7. Event recording
    """

    message_id = payload.get("message_id")
    phone_number_id = payload.get("phone_number_id")
    contact_phone = payload.get("from")
    message_text = payload.get("text")

    if not message_id or not phone_number_id or not contact_phone:
        raise ValueError("Invalid WhatsApp payload")

    try:

        # ---------------------------
        # 1️⃣ Idempotency check
        # ---------------------------
        existing_inquiry = (
            db.query(Inquiry)
            .filter_by(idempotency_key=message_id)
            .first()
        )

        if existing_inquiry:
            return {
                "status": "duplicate",
                "inquiry_id": existing_inquiry.id,
            }

        # ---------------------------
        # 2️⃣ Tenant lookup
        # ---------------------------
        tenant = (
            db.query(Tenant)
            .join(Tenant.whatsapp_accounts)
            .filter(
                Tenant.whatsapp_accounts.any(
                    phone_number_id=phone_number_id
                )
            )
            .first()
        )

        if not tenant:
            raise ValueError("Tenant not found")

        # ---------------------------
        # 3️⃣ Coexistence check
        # ---------------------------
        if tenant.coexistence_status != CoexistenceStatus.ACTIVE:
            raise PermissionError(
                "Tenant not active for inbound messages"
            )

        # ---------------------------
        # 4️⃣ Contact lookup / create
        # ---------------------------
        contact = (
            db.query(Contact)
            .filter_by(
                phone_number=contact_phone,
                tenant_id=tenant.id,
            )
            .first()
        )

        if not contact:
            contact = Contact(
                id=str(uuid.uuid4()),
                phone_number=contact_phone,
                tenant_id=tenant.id,
                name=contact_phone,
            )

            db.add(contact)
            db.flush()

        # ---------------------------
        # 5️⃣ Select WhatsApp account
        # ---------------------------
        whatsapp_account = next(
            (
                wa
                for wa in tenant.whatsapp_accounts
                if wa.phone_number_id == phone_number_id
            ),
            None,
        )

        if not whatsapp_account:
            raise ValueError("WhatsApp account not found")

        # ---------------------------
        # 6️⃣ Create Inquiry
        # ---------------------------
        inquiry = Inquiry(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            contact_id=contact.id,
            whatsapp_account_id=whatsapp_account.id,
            message=message_text,
            idempotency_key=message_id,
            status="new",
        )

        db.add(inquiry)
        db.flush()

        # ---------------------------
        # 7️⃣ Record Event
        # ---------------------------
        event = Event(
            id=str(uuid.uuid4()),
            event_type=EventType.INQUIRY_CREATED,
            actor=ActorType.CUSTOMER,
            tenant_id=tenant.id,
            contact_id=contact.id,
            inquiry_id=inquiry.id,
            payload=payload,
        )

        db.add(event)

        db.commit()

        return {
            "status": "ok",
            "inquiry_id": inquiry.id,
        }

    except Exception:
        db.rollback()
        raise


# =========================================================
# MoMo Webhook Handler
# =========================================================
def handle_momo_webhook(payload: dict, db: Session) -> dict:
    """
    Handles inbound MoMo payment notifications.

    Flow:
    1. Idempotency check via transaction_id
    2. Tenant lookup
    3. Coexistence validation
    4. Record payment event
    """

    transaction_id = payload.get("transaction_id")

    if not transaction_id:
        raise ValueError("Transaction ID missing")

    try:

        # ---------------------------
        # 1️⃣ Idempotency check
        # ---------------------------
        existing_event = (
            db.query(Event)
            .filter_by(idempotency_key=transaction_id)
            .first()
        )

        if existing_event:
            return {
                "status": "duplicate",
                "event_id": existing_event.id,
            }

        # ---------------------------
        # 2️⃣ Find tenant
        # ---------------------------
        tenant_id = payload.get("tenant_id")

        tenant = db.query(Tenant).filter_by(id=tenant_id).first()

        if not tenant:
            raise ValueError("Tenant not found")

        # ---------------------------
        # 3️⃣ Coexistence check
        # ---------------------------
        if tenant.coexistence_status != CoexistenceStatus.ACTIVE:
            raise PermissionError(
                "Tenant not active for MoMo transactions"
            )

        # ---------------------------
        # 4️⃣ Record payment event
        # ---------------------------
        event = Event(
            id=str(uuid.uuid4()),
            event_type=EventType.PAYMENT_RECORDED,
            actor=ActorType.SYSTEM,
            tenant_id=tenant.id,
            payload=payload,
            idempotency_key=transaction_id,
        )

        db.add(event)

        db.commit()

        return {
            "status": "ok",
            "event_id": event.id,
        }

    except Exception:
        db.rollback()
        raise