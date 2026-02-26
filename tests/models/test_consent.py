import pytest
from sqlalchemy.orm import Session
from app.models.consent import Consent
from app.models.tenant import Tenant

def test_create_consent(db_session: Session):
    # Create a tenant first (foreign key)
    tenant = Tenant(id="tenant_1", name="Tenant One")
    db_session.add(tenant)
    db_session.commit()

    consent = Consent(
        id="consent_1",
        tenant_id=tenant.id,
        contact_id=None,
        consented=True,  # updated to match model
    )
    db_session.add(consent)
    db_session.commit()

    retrieved = db_session.get(Consent, "consent_1")
    assert retrieved is not None
    assert retrieved.tenant_id == tenant.id
    assert retrieved.consented is True