import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.contact import Contact
from app.models.inquiry import Inquiry
from app.models.event import Event
from app.models.whatsapp_account import WhatsAppAccount
from app.core.enums import CoexistenceStatus
import uuid

@pytest.fixture
def client(db_session):
    """FastAPI test client with db session override"""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def tenant(db_session):
    """Create a tenant with ACTIVE coexistence status and a WA account"""
    unique_id = str(uuid.uuid4())[:8]
    t = Tenant(
        id=str(uuid.uuid4()),
        name=f"Demo Tenant {unique_id}",
        coexistence_status=CoexistenceStatus.ACTIVE
    )
    db_session.add(t)
    db_session.flush()

    # Add WhatsApp account
    wa = WhatsAppAccount(
        id=str(uuid.uuid4()),
        tenant_id=t.id,
        phone_number=f"+250700000{unique_id}"
    )
    db_session.add(wa)
    db_session.flush()
    db_session.refresh(t)
    return t


def test_whatsapp_webhook_creates_inquiry(client, db_session, tenant):
    payload = {
        "message_id": "msg-001",
        "from": "+250788000001",
        "to": tenant.whatsapp_accounts[0].phone_number,
        "text": "Hello Phase 1"
    }

    # Hit webhook
    response = client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

    # Check inquiry created
    inquiry = db_session.query(Inquiry).filter_by(id=data["inquiry_id"]).first()
    assert inquiry is not None
    assert inquiry.message == "Hello Phase 1"
    assert inquiry.tenant_id == tenant.id

    # Check contact created
    contact = db_session.query(Contact).filter_by(phone_number=payload["from"], tenant_id=tenant.id).first()
    assert contact is not None

    # Check event created
    event = db_session.query(Event).filter_by(inquiry_id=inquiry.id).first()
    assert event is not None
    assert event.event_type.name == "INQUIRY_CREATED"


def test_whatsapp_webhook_duplicate_message(client, db_session, tenant):
    """Sending the same message twice should not create duplicate inquiries"""
    payload = {
        "message_id": "msg-dup",
        "from": "+250788000002",
        "to": tenant.whatsapp_accounts[0].phone_number,
        "text": "Duplicate test"
    }

    # First request
    response1 = client.post("/webhooks/whatsapp", json=payload)
    assert response1.status_code == 200
    inquiry_id = response1.json()["inquiry_id"]

    # Second request with same idempotency_key
    response2 = client.post("/webhooks/whatsapp", json=payload)
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["status"] == "duplicate"
    assert data2["inquiry_id"] == inquiry_id


def test_whatsapp_webhook_inactive_tenant(client, db_session):
    """Tenant not active should get 403"""
    inactive_tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Inactive Tenant",
        coexistence_status=CoexistenceStatus.PENDING
    )
    db_session.add(inactive_tenant)
    db_session.flush()

    # Add WA account for inactive tenant
    wa = WhatsAppAccount(
        id=str(uuid.uuid4()),
        tenant_id=inactive_tenant.id,
        phone_number="+250700000002"
    )
    db_session.add(wa)
    db_session.flush()

    payload = {
        "message_id": "msg-inactive",
        "from": "+250788000003",
        "to": wa.phone_number,
        "text": "Should fail"
    }

    response = client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "Tenant not active for inbound messages"