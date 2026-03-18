# tests/models/test_whatsapp_account.py

import uuid
import pytest
from app.db.models_import import WhatsAppAccount, Tenant


def test_create_whatsapp_account(db_session):
    """Test basic WhatsAppAccount creation."""

    tenant = Tenant(id=str(uuid.uuid4()), name="WA Tenant")
    db_session.add(tenant)
    db_session.commit()

    wa = WhatsAppAccount(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        phone_number="+250788000001",
        phone_number_id="wa_001"
    )

    db_session.add(wa)
    db_session.commit()
    db_session.refresh(wa)

    assert wa.id is not None
    assert wa.phone_number == "+250788000001"
    assert wa.phone_number_id == "wa_001"
    assert wa.tenant.id == tenant.id
    assert wa.created_at is not None


def test_whatsapp_account_unique_phone_number(db_session):
    """phone_number must be unique."""

    tenant = Tenant(id=str(uuid.uuid4()), name="Unique Phone Tenant")
    db_session.add(tenant)
    db_session.commit()

    wa1 = WhatsAppAccount(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        phone_number="+250788000002",
        phone_number_id="wa_002"
    )

    wa2 = WhatsAppAccount(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        phone_number="+250788000002",  # duplicate
        phone_number_id="wa_003"
    )

    db_session.add(wa1)
    db_session.commit()

    db_session.add(wa2)

    with pytest.raises(Exception):
        db_session.commit()


def test_whatsapp_account_unique_phone_number_id(db_session):
    """phone_number_id must be unique (used for webhook routing)."""

    tenant = Tenant(id=str(uuid.uuid4()), name="Unique ID Tenant")
    db_session.add(tenant)
    db_session.commit()

    wa1 = WhatsAppAccount(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        phone_number="+250788000003",
        phone_number_id="wa_004"
    )

    wa2 = WhatsAppAccount(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        phone_number="+250788000004",
        phone_number_id="wa_004"  # duplicate
    )

    db_session.add(wa1)
    db_session.commit()

    db_session.add(wa2)

    with pytest.raises(Exception):
        db_session.commit()


def test_whatsapp_account_requires_fields(db_session):
    """Ensure required fields are enforced."""

    tenant = Tenant(id=str(uuid.uuid4()), name="Required WA Tenant")
    db_session.add(tenant)
    db_session.commit()

    wa = WhatsAppAccount(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        phone_number=None,  # invalid
        phone_number_id="wa_005"
    )

    db_session.add(wa)

    with pytest.raises(Exception):
        db_session.commit()


def test_whatsapp_account_relationship(db_session):
    """Tenant should have access to WhatsApp accounts."""

    tenant = Tenant(id=str(uuid.uuid4()), name="Rel WA Tenant")
    db_session.add(tenant)
    db_session.commit()

    wa = WhatsAppAccount(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        phone_number="+250788000005",
        phone_number_id="wa_006"
    )

    db_session.add(wa)
    db_session.commit()
    db_session.refresh(tenant)

    assert len(tenant.whatsapp_accounts) == 1
    assert tenant.whatsapp_accounts[0].phone_number == "+250788000005"