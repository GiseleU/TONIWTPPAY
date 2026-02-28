# tests/models/test_event.py
from app.models import Tenant, Contact, Inquiry, Order, Event, WhatsAppAccount
from app.core.enums import ActorType, EventType


def test_create_event(db_session):
    tenant = Tenant(id="T007", name="Tenant 7")
    contact = Contact(
        id="C005",
        name="Charlie",
        phone_number="+250700000005",
        tenant_id="T007",
    )
    wa = WhatsAppAccount(
        id="W007",
        phone_number="+250788000007",
        tenant_id="T007",
    )

    inquiry = Inquiry(
        id="I004",
        tenant_id="T007",
        contact_id="C005",
        whatsapp_account_id="W007",
        message="Hello",
        status="confirmed",
    )

    order = Order(
        id="O003",
        tenant_id="T007",
        inquiry_id="I004",
        amount=300,
        customer_name="Charlie",
        customer_phone="+250700000005",
        customer_address=None,
    )

    event = Event(
        id="E001",
        tenant_id="T007",
        event_type=EventType.ORDER_CREATED,
        actor=ActorType.SYSTEM,
        order=order,
    )

    db_session.add_all([tenant, contact, wa, inquiry, order, event])
    db_session.commit()

    assert event.order_id == "O003"