import pytest
from app.models.tenant import Tenant

def test_create_tenant(db_session):
    tenant = Tenant(id="T001", name="Demo Tenant")
    db_session.add(tenant)
    db_session.commit()

    fetched = db_session.get(Tenant, "T001")
    assert fetched is not None
    assert fetched.name == "Demo Tenant"