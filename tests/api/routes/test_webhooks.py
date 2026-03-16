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

# ----------------------------------------
# Fixtures
# ----------------------------------------

@pytest.fixture
def client(db_session):
    """FastAPI test client with db session override"""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def tenant(db_session):
    """Create tenant with ACTIVE coexistence status"""
    unique_id = str(uuid.uuid4())[:8]

    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=f"Demo Tenant {unique_id}",
        coexistence_status=CoexistenceStatus.ACTIVE,
    )
    db_session.add(tenant)
    db_session.flush()

    wa = WhatsAppAccount(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        phone_number=f"+250700000{unique_id}",
        phone_number_id=f"wa-{unique_id}",
    )
    db_session.add(wa)
    db_session.flush()
    db_session.refresh(tenant)

    return tenant

# ----------------------------------------
# WhatsApp Webhook Tests
# ----------------------------------------

def test_whatsapp_webhook_creates_inquiry(client, db_session, tenant):
    wa = tenant.whatsapp_accounts[0]

    payload = {
        "MessageSid": "msg-001",
        "From": "whatsapp:+250788000001",
        "To": f"whatsapp:{wa.phone_number_id}",
        "Body": "Hello Phase 1",
    }

    response = client.post("/webhooks/whatsapp", data=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"

    # Verify Inquiry
    inquiry = db_session.query(Inquiry).filter_by(id=data["inquiry_id"]).first()
    assert inquiry is not None
    assert inquiry.message == "Hello Phase 1"
    assert inquiry.tenant_id == tenant.id

    # Verify Contact
    contact = db_session.query(Contact).filter_by(
        phone_number=payload["From"].replace("whatsapp:", ""),
        tenant_id=tenant.id
    ).first()
    assert contact is not None

    # Verify Event
    event = db_session.query(Event).filter_by(
        inquiry_id=inquiry.id
    ).first()
    assert event is not None
    assert event.event_type.name == "INQUIRY_CREATED"


def test_whatsapp_webhook_duplicate_message(client, db_session, tenant):
    wa = tenant.whatsapp_accounts[0]

    payload = {
        "MessageSid": "msg-dup",
        "From": "whatsapp:+250788000002",
        "To": f"whatsapp:{wa.phone_number_id}",
        "Body": "Duplicate test",
    }

    # First request creates inquiry
    response1 = client.post("/webhooks/whatsapp", data=payload)
    assert response1.status_code == 200
    inquiry_id = response1.json()["inquiry_id"]

    # Second request with same MessageSid should return duplicate
    response2 = client.post("/webhooks/whatsapp", data=payload)
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["status"] == "duplicate"
    assert data2["inquiry_id"] == inquiry_id


def test_whatsapp_webhook_inactive_tenant(client, db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Inactive Tenant",
        coexistence_status=CoexistenceStatus.PENDING,
    )
    db_session.add(tenant)
    db_session.flush()

    wa = WhatsAppAccount(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        phone_number="+250700000002",
        phone_number_id="wa-inactive",
    )
    db_session.add(wa)
    db_session.flush()

    payload = {
        "MessageSid": "msg-inactive",
        "From": "whatsapp:+250788000003",
        "To": f"whatsapp:{wa.phone_number_id}",
        "Body": "Should fail",
    }

    response = client.post("/webhooks/whatsapp", data=payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "Tenant not active for inbound messages"


# ----------------------------------------
# MoMo Webhook Tests
# ----------------------------------------

def test_momo_webhook_creates_event(client, db_session, tenant):
    payload = {
        "transaction_id": "txn-001",
        "tenant_id": tenant.id,
        "amount": 100,
    }

    response = client.post("/webhooks/momo", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"

    event = db_session.query(Event).filter_by(id=data["event_id"]).first()
    assert event is not None
    assert event.tenant_id == tenant.id
    assert event.payload["transaction_id"] == "txn-001"


def test_momo_webhook_duplicate_event(client, db_session, tenant):
    payload = {
        "transaction_id": "txn-dup",
        "tenant_id": tenant.id,
        "amount": 100,
    }

    # First request
    response1 = client.post("/webhooks/momo", json=payload)
    assert response1.status_code == 200
    event_id = response1.json()["event_id"]

    # Duplicate request
    response2 = client.post("/webhooks/momo", json=payload)
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["status"] == "duplicate"
    assert data2["event_id"] == event_id


def test_momo_webhook_inactive_tenant(client, db_session):
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Inactive Tenant",
        coexistence_status=CoexistenceStatus.PENDING,
    )
    db_session.add(tenant)
    db_session.flush()

    payload = {
        "transaction_id": "txn-inactive",
        "tenant_id": tenant.id,
        "amount": 100,
    }

    response = client.post("/webhooks/momo", json=payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "Tenant not active for MoMo transactions"