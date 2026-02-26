from app.models.order import Order
from app.models.inquiry import Inquiry
from app.models.tenant import Tenant
from app.models.contact import Contact
from app.models.whatsapp_account import WhatsAppAccount

def test_create_order(db_session):
    tenant = Tenant(id="T005", name="Tenant 5")
    contact = Contact(id="C003", name="Bob", phone_number="+250700000003", tenant_id="T005")
    whatsapp_account = WhatsAppAccount(id="W005", phone_number="+250788000005", tenant_id="T005")
    inquiry = Inquiry(id="I002", tenant_id="T005", contact_id="C003", whatsapp_account_id="W005", message="Need 10 units")
    db_session.add_all([tenant, contact, whatsapp_account, inquiry])
    db_session.commit()

    order = Order(id="O001", tenant_id="T005", contact_id="C003", inquiry_id="I002", total_amount=150.0)
    db_session.add(order)
    db_session.commit()

    fetched = db_session.get(Order, "O001")
    assert fetched.inquiry_id == inquiry.id
    assert fetched.contact_id == contact.id
    assert fetched.total_amount == 150.0
