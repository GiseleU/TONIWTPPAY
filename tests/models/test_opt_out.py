import pytest
from sqlalchemy.orm import Session
from app.models.opt_out import OptOut
from app.models.tenant import Tenant

def test_create_opt_out(db_session: Session):
    # Create a tenant first (foreign key)
    tenant = Tenant(id="tenant_2", name="Tenant Two")
    db_session.add(tenant)
    db_session.commit()

    opt_out = OptOut(
        id="optout_1",
        tenant_id=tenant.id,
        contact_id=None,
        reason="do_not_contact",
    )
    db_session.add(opt_out)
    db_session.commit()

    retrieved = db_session.get(OptOut, "optout_1")
    assert retrieved is not None
    assert retrieved.tenant_id == tenant.id
    assert retrieved.reason == "do_not_contact"