# tests/models/test_payment.py
from app.models import Tenant, Contact, Inquiry, Order, Payment, WhatsAppAccount


def test_create_payment(db_session):
    tenant = Tenant(id="T006", name="Tenant 6")
    contact = Contact(
        id="C004",
        name="Eve",
        phone_number="+250700000004",
        tenant_id="T006",
    )

    wa = WhatsAppAccount(
        id="W006",
        phone_number="+250788000006",
        tenant_id="T006",
        phone_number_id="wa_test_001"
    )

    inquiry = Inquiry(
        id="I003",
        tenant_id="T006",
        contact_id="C004",
        whatsapp_account_id="W006",
        message="Order inquiry",
        status="confirmed",
    )

    order = Order(
        id="O002",
        tenant_id="T006",
        inquiry_id="I003",
        amount=200,
        customer_name="Eve",
        customer_phone="+250700000004",
        customer_address=None,
        status="completed",
    )

    payment = Payment(
        id="P001",
        tenant_id="T006",
        order_id="O002",
        amount=200,
        verified_by="staff_1",
        method="cash",
        notes="Full payment",
    )

    db_session.add_all([tenant, contact, wa, inquiry, order, payment])
    db_session.commit()

    assert payment.order_id == "O002"
