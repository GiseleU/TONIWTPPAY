from app.models.inquiry import Inquiry
from app.models.tenant import Tenant
from app.models.contact import Contact
from app.models.whatsapp_account import WhatsAppAccount

def test_create_inquiry(db_session):
    tenant = Tenant(id="T004", name="Tenant 4")
    contact = Contact(id="C002", name="Alice", phone_number="+250700000002", tenant_id="T004")
    whatsapp_account = WhatsAppAccount(id="W004", phone_number="+250788000004", tenant_id="T004", phone_number_id="wa_test_001")
    db_session.add_all([tenant, contact, whatsapp_account])
    db_session.commit()

    inquiry = Inquiry(id="I001", tenant_id="T004", contact_id="C002", whatsapp_account_id="W004", message="Interested in product")
    db_session.add(inquiry)
    db_session.commit()

    fetched = db_session.get(Inquiry, "I001")
    assert fetched.contact_id == contact.id
    assert fetched.tenant_id == tenant.id
    assert fetched.whatsapp_account_id == whatsapp_account.id
