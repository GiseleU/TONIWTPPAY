from app.models.whatsapp_account import WhatsAppAccount
from app.models.tenant import Tenant

def test_create_whatsapp_account(db_session):
    tenant = Tenant(id="T003", name="Tenant 3")
    db_session.add(tenant)
    db_session.commit()

    account = WhatsAppAccount(id="W001", phone_number="+250788000001", tenant_id="T003", phone_number_id="wa_test_001")
    db_session.add(account)
    db_session.commit()

    fetched = db_session.get(WhatsAppAccount, "W001")
    assert fetched is not None
    assert fetched.tenant_id == tenant.id