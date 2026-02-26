from app.models.payment import Payment
from app.models.order import Order
from app.models.tenant import Tenant
from app.models.contact import Contact
from app.models.inquiry import Inquiry
from app.models.whatsapp_account import WhatsAppAccount

def test_create_payment(db_session):
    tenant = Tenant(id="T006", name="Tenant 6")
    contact = Contact(id="C004", name="Eve", phone_number="+250700000004", tenant_id="T006")
    whatsapp_account = WhatsAppAccount(id="W006", phone_number="+250788000006", tenant_id="T006")
    inquiry = Inquiry(id="I003", tenant_id="T006", contact_id="C004", whatsapp_account_id="W006", message="Order inquiry")
    order = Order(id="O002", tenant_id="T006", contact_id="C004", inquiry_id="I003", total_amount=200)
    db_session.add_all([tenant, contact, whatsapp_account, inquiry, order])
    db_session.commit()

    payment = Payment(id="P001", tenant_id="T006", contact_id="C004", order_id="O002", amount=200)
    db_session.add(payment)
    db_session.commit()

    fetched = db_session.get(Payment, "P001")
    assert fetched.order_id == order.id
    assert fetched.amount == 200
