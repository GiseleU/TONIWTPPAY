# tests/models/test_order.py
from app.models import Tenant, Contact, Inquiry, Order, WhatsAppAccount


def test_create_order_from_confirmed_inquiry(db_session):
    tenant = Tenant(id="T005", name="Tenant 5")

    contact = Contact(
        id="C003",
        name="Bob",
        phone_number="+250700000003",
        tenant_id="T005",
    )

    wa = WhatsAppAccount(
        id="W005",
        phone_number="+250788000005",
        phone_number_id="phone_005",
        tenant_id="T005",
    )

    inquiry = Inquiry(
        id="I002",
        tenant_id="T005",
        contact_id="C003",
        whatsapp_account_id="W005",
        message="Need 10 units",
        status="confirmed",
    )

    order = Order(
        id="O001",
        tenant_id="T005",
        inquiry_id="I002",
        amount=150.00,
        customer_name="Bob",
        customer_phone="+250700000003",
        customer_address="Kigali",
    )

    db_session.add_all([tenant, contact, wa, inquiry, order])
    db_session.commit()

    fetched = db_session.get(Order, "O001")
    assert fetched.amount == 150.00
    assert fetched.customer_name == "Bob"
    assert fetched.inquiry_id == "I002"