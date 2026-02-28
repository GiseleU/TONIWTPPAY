# import pytest
# from unittest.mock import MagicMock
# from sqlalchemy.orm import Session
# from app.services.webhook_service import handle_whatsapp_message, handle_momo_webhook
# from app.core.enums import CoexistenceStatus


# @pytest.fixture
# def db_mock():
#     """Mocked SQLAlchemy session."""
#     return MagicMock(spec=Session)


# @pytest.fixture
# def tenant_active():
#     """Sample active tenant object."""
#     tenant = MagicMock()
#     tenant.id = "tenant-123"
#     tenant.coexistence_status = CoexistenceStatus.ACTIVE
#     tenant.whatsapp_accounts = [MagicMock(id="wa-1", phone_number="+123456789")]
#     return tenant


# @pytest.fixture
# def contact_mock():
#     """Sample contact object."""
#     contact = MagicMock()
#     contact.id = "contact-123"
#     contact.phone_number = "+1987654321"
#     contact.tenant_id = "tenant-123"
#     return contact


# def test_whatsapp_message_creates_inquiry(db_mock, tenant_active):
#     payload = {
#         "message_id": "msg-001",
#         "to": "+123456789",
#         "from": "+1987654321",
#         "text": "Hello"
#     }

#     # Mock DB queries
#     db_mock.query().filter_by().first.side_effect = [None, None]  # No existing inquiry/contact
#     db_mock.query().join().filter().first.return_value = tenant_active

#     result = handle_whatsapp_message(payload, db_mock)

#     assert result["status"] == "ok"
#     assert "inquiry_id" in result
#     assert db_mock.add.call_count >= 2  # contact + inquiry + event
#     assert db_mock.commit.called


# def test_whatsapp_duplicate_inquiry(db_mock, tenant_active):
#     payload = {"message_id": "msg-001", "to": "+123456789", "from": "+1987654321", "text": "Hello"}

#     # Mock DB returns an existing inquiry
#     existing_inquiry = MagicMock(id="inq-123")
#     db_mock.query().filter_by().first.return_value = existing_inquiry

#     result = handle_whatsapp_message(payload, db_mock)
#     assert result["status"] == "duplicate"
#     assert result["inquiry_id"] == "inq-123"


# def test_whatsapp_inactive_tenant_raises(db_mock):
#     tenant = MagicMock()
#     tenant.coexistence_status = CoexistenceStatus.PENDING
#     tenant.whatsapp_accounts = [MagicMock(id="wa-1", phone_number="+123456789")]

#     payload = {"message_id": "msg-001", "to": "+123456789", "from": "+1987654321", "text": "Hi"}

#     db_mock.query().join().filter().first.return_value = tenant

#     with pytest.raises(PermissionError):
#         handle_whatsapp_message(payload, db_mock)


# def test_momo_webhook_creates_event(db_mock):
#     payload = {"transaction_id": "txn-001", "tenant_id": "tenant-123", "amount": 100}

#     tenant = MagicMock()
#     tenant.id = "tenant-123"
#     tenant.coexistence_status = CoexistenceStatus.ACTIVE

#     db_mock.query().filter_by().first.side_effect = [None, tenant]  # No duplicate event, tenant exists

#     result = handle_momo_webhook(payload, db_mock)
#     assert result["status"] == "ok"
#     assert "event_id" in result
#     assert db_mock.add.called
#     assert db_mock.commit.called


# def test_momo_webhook_duplicate_event(db_mock):
#     payload = {"transaction_id": "txn-001", "tenant_id": "tenant-123", "amount": 100}
#     existing_event = MagicMock(id="event-123")
#     db_mock.query().filter_by().first.return_value = existing_event

#     result = handle_momo_webhook(payload, db_mock)
#     assert result["status"] == "duplicate"
#     assert result["event_id"] == "event-123"


# def test_momo_inactive_tenant_raises(db_mock):
#     tenant = MagicMock()
#     tenant.coexistence_status = CoexistenceStatus.PENDING
#     payload = {"transaction_id": "txn-001", "tenant_id": "tenant-123", "amount": 100}

#     db_mock.query().filter_by().first.side_effect = [None, tenant]

#     with pytest.raises(PermissionError):
#         handle_momo_webhook(payload, db_mock)


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
        coexistence_status=CoexistenceStatus.ACTIVE
    )
    tenant.whatsapp_accounts = [MagicMock(id="wa-1", phone_number="+123456789")]
    return tenant

@pytest.fixture
def tenant_inactive():
    tenant = Tenant(
        id="tenant-456",
        name="Inactive Tenant",
        coexistence_status=CoexistenceStatus.PENDING
    )
    tenant.whatsapp_accounts = [MagicMock(id="wa-2", phone_number="+987654321")]
    return tenant

def test_whatsapp_message_creates_inquiry(db_mock, tenant_active):
    payload = {"message_id": "msg-001", "to": "+123456789", "from": "+1987654321", "text": "Hello"}

    db_mock.query().filter_by().first.side_effect = [None, None]
    db_mock.query().join().filter().first.return_value = tenant_active

    result = handle_whatsapp_message(payload, db_mock)
    assert result["status"] == "ok"
    assert "inquiry_id" in result
    assert db_mock.add.call_count >= 2
    assert db_mock.commit.called

def test_whatsapp_duplicate_inquiry(db_mock, tenant_active):
    payload = {"message_id": "msg-001", "to": "+123456789", "from": "+1987654321", "text": "Hello"}
    existing_inquiry = MagicMock(id="inq-123")
    db_mock.query().filter_by().first.return_value = existing_inquiry

    result = handle_whatsapp_message(payload, db_mock)
    assert result["status"] == "duplicate"
    assert result["inquiry_id"] == "inq-123"

def test_whatsapp_inactive_tenant_raises(db_mock, tenant_inactive):
    payload = {"message_id": "msg-002", "to": "+987654321", "from": "+1987654322", "text": "Hi"}
    db_mock.query().filter_by().first.side_effect = [None, None]  # No existing inquiry/contact
    db_mock.query().join().filter().first.return_value = tenant_inactive

    with pytest.raises(PermissionError):
        handle_whatsapp_message(payload, db_mock)

def test_momo_webhook_creates_event(db_mock, tenant_active):
    payload = {"transaction_id": "txn-001", "tenant_id": "tenant-123", "amount": 100}
    db_mock.query().filter_by().first.side_effect = [None, tenant_active]

    result = handle_momo_webhook(payload, db_mock)
    assert result["status"] == "ok"
    assert "event_id" in result
    assert db_mock.add.called
    assert db_mock.commit.called

def test_momo_webhook_duplicate_event(db_mock, tenant_active):
    payload = {"transaction_id": "txn-001", "tenant_id": "tenant-123", "amount": 100}
    existing_event = MagicMock(id="event-123")
    db_mock.query().filter_by().first.return_value = existing_event

    result = handle_momo_webhook(payload, db_mock)
    assert result["status"] == "duplicate"
    assert result["event_id"] == "event-123"

def test_momo_inactive_tenant_raises(db_mock, tenant_inactive):
    payload = {"transaction_id": "txn-002", "tenant_id": "tenant-456", "amount": 100}
    db_mock.query().filter_by().first.side_effect = [None, tenant_inactive]

    with pytest.raises(PermissionError):
        handle_momo_webhook(payload, db_mock)
