from app.models.contact import Contact
from app.models.tenant import Tenant

def test_create_contact(db_session):
    tenant = Tenant(id="T002", name="Tenant 2")
    db_session.add(tenant)
    db_session.commit()

    contact = Contact(id="C001", name="John Doe", phone_number="+250700000001", tenant_id="T002")
    db_session.add(contact)
    db_session.commit()

    fetched = db_session.get(Contact, "C001")
    assert fetched is not None
    assert fetched.tenant_id == tenant.id