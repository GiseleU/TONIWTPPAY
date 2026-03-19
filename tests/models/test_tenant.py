# tests/models/test_tenant.py

import pytest
from app.db.models_import import Tenant
from app.core.enums import CoexistenceStatus
import uuid


def test_create_tenant(db_session):
    """Test basic tenant creation."""
    tenant = Tenant(id="T001", name="Demo Tenant")
    db_session.add(tenant)
    db_session.commit()

    fetched = db_session.get(Tenant, "T001")

    assert fetched is not None
    assert fetched.name == "Demo Tenant"
    assert fetched.phone_number is None


def test_tenant_defaults(db_session):
    """Test default values are correctly set."""
    tenant = Tenant(id=str(uuid.uuid4()), name="Default Tenant")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    # Default enum
    assert tenant.coexistence_status == CoexistenceStatus.PENDING

    # Auto timestamp
    assert tenant.created_at is not None


def test_tenant_unique_name_constraint(db_session):
    """Test that tenant name must be unique."""
    tenant1 = Tenant(id="T002", name="UniqueTenant")
    tenant2 = Tenant(id="T003", name="UniqueTenant")  # same name

    db_session.add(tenant1)
    db_session.commit()

    db_session.add(tenant2)

    with pytest.raises(Exception):
        db_session.commit()


def test_tenant_with_phone_number(db_session):
    """Test optional phone_number field."""
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Phone Tenant",
        phone_number="250700000001"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    assert tenant.phone_number == "250700000001"


def test_tenant_relationships_empty(db_session):
    """Ensure relationships initialize as empty lists."""
    tenant = Tenant(id=str(uuid.uuid4()), name="Rel Tenant")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    assert tenant.transactions == []
    assert tenant.transaction_items == []
    assert tenant.payments == []
    assert tenant.daily_summaries == []
    assert tenant.events == []