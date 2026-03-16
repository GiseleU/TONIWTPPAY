import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.services.webhook_service import handle_whatsapp_message, handle_momo_webhook
from app.core.enums import CoexistenceStatus
from app.models.tenant import Tenant


@pytest.fixture
def db_mock():
    return MagicMock(spec=Session)


@pytest.fixture
def tenant_active():
    tenant = Tenant(
        id="tenant-123",
        name="Active Tenant",
        coexistence_status=CoexistenceStatus.ACTIVE,
    )
    tenant.whatsapp_accounts = [
        MagicMock(id="wa-1", phone_number_id="+123456789")
    ]
    return tenant


@pytest.fixture
def tenant_inactive():
    tenant = Tenant(
        id="tenant-456",
        name="Inactive Tenant",
        coexistence_status=CoexistenceStatus.PENDING,
    )
    tenant.whatsapp_accounts = [
        MagicMock(id="wa-2", phone_number_id="+987654321")
    ]
    return tenant


# --------------------------------------------------
# WHATSAPP MESSAGE TESTS
# --------------------------------------------------

def test_whatsapp_message_creates_inquiry(db_mock, tenant_active):

    payload = {
        "message_id": "msg-001",
        "phone_number_id": "+123456789",
        "from": "+1987654321",
        "text": "Hello",
    }

    # Duplicate inquiry check
    query_duplicate = MagicMock()
    query_duplicate.filter_by.return_value.first.return_value = None

    # Tenant lookup
    query_tenant = MagicMock()
    query_tenant.join.return_value.filter.return_value.first.return_value = tenant_active

    # Contact lookup
    query_contact = MagicMock()
    query_contact.filter_by.return_value.first.return_value = None

    db_mock.query.side_effect = [
        query_duplicate,
        query_tenant,
        query_contact,
    ]

    result = handle_whatsapp_message(payload, db_mock)

    assert result["status"] == "ok"
    assert "inquiry_id" in result
    assert db_mock.add.call_count >= 2
    assert db_mock.commit.called


def test_whatsapp_duplicate_inquiry(db_mock):

    payload = {
        "message_id": "msg-001",
        "phone_number_id": "+123456789",
        "from": "+1987654321",
        "text": "Hello",
    }

    existing_inquiry = MagicMock(id="inq-123")

    query_duplicate = MagicMock()
    query_duplicate.filter_by.return_value.first.return_value = existing_inquiry

    db_mock.query.return_value = query_duplicate

    result = handle_whatsapp_message(payload, db_mock)

    assert result["status"] == "duplicate"
    assert result["inquiry_id"] == "inq-123"


def test_whatsapp_inactive_tenant_raises(db_mock, tenant_inactive):

    payload = {
        "message_id": "msg-002",
        "phone_number_id": "+987654321",
        "from": "+1987654322",
        "text": "Hi",
    }

    query_duplicate = MagicMock()
    query_duplicate.filter_by.return_value.first.return_value = None

    query_tenant = MagicMock()
    query_tenant.join.return_value.filter.return_value.first.return_value = tenant_inactive

    db_mock.query.side_effect = [
        query_duplicate,
        query_tenant,
    ]

    with pytest.raises(PermissionError):
        handle_whatsapp_message(payload, db_mock)


# --------------------------------------------------
# MOMO WEBHOOK TESTS
# --------------------------------------------------

def test_momo_webhook_creates_event(db_mock, tenant_active):

    payload = {
        "transaction_id": "txn-001",
        "tenant_id": "tenant-123",
        "amount": 100,
    }

    # Duplicate event check
    query_event = MagicMock()
    query_event.filter_by.return_value.first.return_value = None

    # Tenant lookup
    query_tenant = MagicMock()
    query_tenant.filter_by.return_value.first.return_value = tenant_active

    db_mock.query.side_effect = [
        query_event,
        query_tenant,
    ]

    result = handle_momo_webhook(payload, db_mock)

    assert result["status"] == "ok"
    assert "event_id" in result
    assert db_mock.add.called
    assert db_mock.commit.called


def test_momo_webhook_duplicate_event(db_mock):

    payload = {
        "transaction_id": "txn-001",
        "tenant_id": "tenant-123",
        "amount": 100,
    }

    existing_event = MagicMock(id="event-123")

    query_event = MagicMock()
    query_event.filter_by.return_value.first.return_value = existing_event

    db_mock.query.return_value = query_event

    result = handle_momo_webhook(payload, db_mock)

    assert result["status"] == "duplicate"
    assert result["event_id"] == "event-123"


def test_momo_inactive_tenant_raises(db_mock, tenant_inactive):

    payload = {
        "transaction_id": "txn-002",
        "tenant_id": "tenant-456",
        "amount": 100,
    }

    query_event = MagicMock()
    query_event.filter_by.return_value.first.return_value = None

    query_tenant = MagicMock()
    query_tenant.filter_by.return_value.first.return_value = tenant_inactive

    db_mock.query.side_effect = [
        query_event,
        query_tenant,
    ]

    with pytest.raises(PermissionError):
        handle_momo_webhook(payload, db_mock)
