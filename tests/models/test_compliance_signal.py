# Tests for ComplianceSignal model

import pytest
from app.models import ComplianceSignal, Tenant, Contact, WhatsAppAccount


def test_compliance_signal_creation(db_session):
    tenant = Tenant(id="T001", name="Test Tenant")
    contact = Contact(id="C001", tenant_id=tenant.id, name="Test", phone_number="123")
    wa = WhatsAppAccount(id="WA001", tenant_id=tenant.id, phone_number="456", phone_number_id="wa_test_001")
    db_session.add(tenant)
    db_session.add(contact)
    db_session.add(wa)

    signal = ComplianceSignal(
        id="CS001",
        tenant_id=tenant.id,
        event_type="opt_out",
        contact_id=contact.id,
        whatsapp_account_id=wa.id,
            details='{"reason": "user request"}'
    )
    db_session.add(signal)
    db_session.commit()

    assert signal.id == "CS001"
    assert signal.event_type == "opt_out"
