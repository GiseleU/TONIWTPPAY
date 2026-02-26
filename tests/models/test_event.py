from app.models.event import Event
from app.models.tenant import Tenant
from app.models.contact import Contact
from app.models.inquiry import Inquiry
from app.models.order import Order
from app.models.whatsapp_account import WhatsAppAccount
from app.core.enums import EventType, ActorType

def test_create_event(db_session):
    tenant = Tenant(id="T007", name="Tenant 7")
    contact = Contact(id="C005", name="Charlie", phone_number="+250700000005", tenant_id="T007")
    whatsapp_account = WhatsAppAccount(id="W007", phone_number="+250788000007", tenant_id="T007")
    inquiry = Inquiry(id="I004", tenant_id="T007", contact_id="C005", whatsapp_account_id="W007", message="Hello")
    order = Order(id="O003", tenant_id="T007", contact_id="C005", inquiry_id="I004", total_amount=300)
    db_session.add_all([tenant, contact, whatsapp_account, inquiry, order])
    db_session.commit()

    event = Event(
        id="E001",
        event_type=EventType.ORDER_CREATED,
        actor=ActorType.CUSTOMER,
        tenant_id="T007",
        contact_id="C005",
        inquiry_id="I004",
        order_id="O003",
        payload={"info": "Order created"}
    )
    db_session.add(event)
    db_session.commit()

    fetched = db_session.get(Event, "E001")
    assert fetched.order_id == order.id
    assert fetched.payload["info"] == "Order created"
