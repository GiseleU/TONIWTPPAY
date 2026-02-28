# tests/api/routes/test_orders.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.inquiry import Inquiry
from app.models.contact import Contact
from app.models.tenant import Tenant
from app.models.whatsapp_account import WhatsAppAccount
from app.models.event import Event, EventType
from app.core.enums import CoexistenceStatus
from app.db.session import get_db
from datetime import datetime

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def setup_inquiry(db_session: Session):
    tenant = Tenant(id="tenant_api", name="Test Tenant", coexistence_status=CoexistenceStatus.ACTIVE)
    db_session.add(tenant)
    db_session.commit()

    contact = Contact(id="C001", name="Eve", phone_number="555000111", tenant_id=tenant.id)
    db_session.add(contact)
    db_session.commit()

    whatsapp_account = WhatsAppAccount(id="W001", phone_number="+250788000001", tenant_id=tenant.id)
    db_session.add(whatsapp_account)
    db_session.commit()

    inquiry = Inquiry(
        id="TAPI123",
        tenant_id=tenant.id,
        contact_id=contact.id,
        whatsapp_account_id=whatsapp_account.id,
        message="Test inquiry message",
        status="confirmed",
        amount=150.0
    )
    db_session.add(inquiry)
    db_session.commit()

    return inquiry, contact


def test_create_order_success(client: TestClient, db_session: Session, setup_inquiry):
    inquiry, _ = setup_inquiry

    response = client.post("/orders/from-inquiry", json={
        "inquiry_id": inquiry.id,
        "tenant_id": "tenant_api",
        "customer_name": "Eve",
        "customer_phone": "555000111",
        "customer_address": "101 Main St"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["id"].startswith("O")
    assert data["inquiry_id"] == inquiry.id

    # Check event logged
    event = db_session.query(Event).filter_by(order_id=data["id"], event_type=EventType.ORDER_CREATED).first()
    assert event is not None


def test_create_order_missing_customer_name(client: TestClient, db_session: Session, setup_inquiry):
    inquiry, _ = setup_inquiry

    response = client.post("/orders/from-inquiry", json={
        "inquiry_id": inquiry.id,
        "tenant_id": "tenant_api",
        "customer_name": "",
        "customer_phone": "555000111"
    })

    assert response.status_code == 400
    assert "Customer name is required" in response.json()["detail"]

    # Check failure event logged
    event = db_session.query(Event).filter_by(
        inquiry_id=inquiry.id, event_type=EventType.ORDER_CREATION_FAILED
    ).first()
    assert event is not None


def test_create_order_duplicate(client: TestClient, db_session: Session, setup_inquiry):
    inquiry, _ = setup_inquiry

    # First creation succeeds
    client.post("/orders/from-inquiry", json={
        "inquiry_id": inquiry.id,
        "tenant_id": "tenant_api",
        "customer_name": "Eve",
        "customer_phone": "555000111"
    })

    # Second creation fails
    response = client.post("/orders/from-inquiry", json={
        "inquiry_id": inquiry.id,
        "tenant_id": "tenant_api",
        "customer_name": "Eve",
        "customer_phone": "555000111"
    })

    assert response.status_code == 400
    assert "already has an order" in response.json()["detail"]

    # Check failure event
    event = db_session.query(Event).filter_by(
        inquiry_id=inquiry.id, event_type=EventType.ORDER_CREATION_FAILED
    ).first()
    assert event is not None


def test_get_order_success(client: TestClient, db_session: Session, setup_inquiry):
    inquiry, _ = setup_inquiry

    post_resp = client.post("/orders/from-inquiry", json={
        "inquiry_id": inquiry.id,
        "tenant_id": "tenant_api",
        "customer_name": "Eve",
        "customer_phone": "555000111"
    })

    order_id = post_resp.json()["id"]

    get_resp = client.get(f"/orders/{order_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == order_id


def test_list_orders_by_tenant(client: TestClient, db_session: Session, setup_inquiry):
    inquiry, _ = setup_inquiry

    # Create multiple orders
    client.post("/orders/from-inquiry", json={
        "inquiry_id": inquiry.id,
        "tenant_id": "tenant_api",
        "customer_name": "Eve",
        "customer_phone": "555000111"
    })

    resp = client.get("/orders", params={"tenant_id": "tenant_api"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert all(o["tenant_id"] == "tenant_api" for o in data)


def test_cross_tenant_access_denied(client: TestClient, db_session: Session, setup_inquiry):
    inquiry, _ = setup_inquiry

    # Attempt to create order under wrong tenant
    response = client.post("/orders/from-inquiry", json={
        "inquiry_id": inquiry.id,
        "tenant_id": "other_tenant",
        "customer_name": "Eve",
        "customer_phone": "555000111"
    })
    assert response.status_code == 400
    assert "Inquiry TAPI123 not found" in response.json()["detail"]


def test_invalid_inquiry_status(client: TestClient, db_session: Session):
    # Setup inquiry in pending status
    tenant = Tenant(id="tenant2", name="Tenant 2", coexistence_status=CoexistenceStatus.ACTIVE)
    db_session.add(tenant)
    db_session.commit()

    contact = Contact(id="C002", name="Alice", phone_number="555222333", tenant_id=tenant.id)
    db_session.add(contact)
    db_session.commit()

    whatsapp_account = WhatsAppAccount(id="W002", phone_number="+250788000002", tenant_id=tenant.id)
    db_session.add(whatsapp_account)
    db_session.commit()

    inquiry = Inquiry(
        id="TAPI456",
        tenant_id=tenant.id,
        contact_id=contact.id,
        whatsapp_account_id=whatsapp_account.id,
        message="Pending inquiry",
        status="pending",
        amount=100.0
    )
    db_session.add(inquiry)
    db_session.commit()

    response = client.post("/orders/from-inquiry", json={
        "inquiry_id": inquiry.id,
        "tenant_id": tenant.id,
        "customer_name": "Alice",
        "customer_phone": "555222333"
    })

    assert response.status_code == 400
    assert "must be confirmed before order creation" in response.json()["detail"]