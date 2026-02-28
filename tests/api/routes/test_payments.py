# tests/api/routes/test_payments.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal
from app.models.order import Order
from app.models.contact import Contact
from app.models.tenant import Tenant
from app.models.whatsapp_account import WhatsAppAccount
from app.core.enums import CoexistenceStatus

@pytest.fixture
def setup_order(db_session: Session):
    """Creates a tenant, contact, and completed order for testing payments."""
    tenant = Tenant(id="tenant_test", name="Test Tenant", coexistence_status=CoexistenceStatus.ACTIVE)
    db_session.add(tenant)

    contact = Contact(id="C001", tenant_id=tenant.id, name="Alice", phone_number="5551234")
    db_session.add(contact)

    whatsapp_account = WhatsAppAccount(id="W001", tenant_id=tenant.id, phone_number="+250788000001")
    db_session.add(whatsapp_account)

    order = Order(
        id="O1001",
        tenant_id=tenant.id,
        inquiry_id="T1001",
        amount=100,
        customer_name="Alice",
        customer_phone="5551234",
        status="completed"
    )
    db_session.add(order)
    db_session.commit()
    return tenant, contact, order


def test_record_payment_success(client: TestClient, setup_order, db_session: Session):
    tenant, contact, order = setup_order

    response = client.post(
        "/payments",
        json={
            "order_id": order.id,
            "amount": "100.00",
            "verified_by": "staff_1",
            "method": "momo",
            "notes": "Full payment"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"].startswith("P")
    assert data["order_id"] == order.id
    assert data["amount"] == "100.00"
    assert data["verified_by"] == "staff_1"
    assert data["method"] == "momo"
    assert data["notes"] == "Full payment"

    # Check order status updated
    db_session.refresh(order)
    assert order.status == "paid"


def test_record_payment_invalid_order(client: TestClient, setup_order):
    tenant, contact, order = setup_order

    response = client.post(
        "/payments",
        json={
            "order_id": "O9999",
            "amount": "100.00",
            "verified_by": "staff_1",
            "method": "momo"
        }
    )

    assert response.status_code == 400
    assert "Order O9999 not found" in response.json()["detail"]


def test_record_overpayment(client: TestClient, setup_order):
    tenant, contact, order = setup_order

    # First payment
    client.post(
        "/payments",
        json={
            "order_id": order.id,
            "amount": "60.00",
            "verified_by": "staff_1",
            "method": "momo"
        }
    )

    # Overpayment
    response = client.post(
        "/payments",
        json={
            "order_id": order.id,
            "amount": "50.00",
            "verified_by": "staff_1",
            "method": "momo"
        }
    )

    assert response.status_code == 400
    assert "would exceed order total" in response.json()["detail"]


def test_get_payment(client: TestClient, setup_order):
    tenant, contact, order = setup_order

    # Create payment
    create_response = client.post(
        "/payments",
        json={
            "order_id": order.id,
            "amount": "50.00",
            "verified_by": "staff_1",
            "method": "cash"
        }
    )
    payment_id = create_response.json()["id"]

    # Get payment
    response = client.get(f"/payments/{payment_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == payment_id
    assert data["amount"] == "50.00"


def test_get_payment_not_found(client: TestClient, setup_order):
    tenant, contact, order = setup_order

    response = client.get("/payments/P9999")
    assert response.status_code == 404


def test_list_payments_for_order(client: TestClient, setup_order):
    tenant, contact, order = setup_order

    # Create payments
    client.post(
        "/payments",
        json={
            "order_id": order.id,
            "amount": "30.00",
            "verified_by": "staff_1",
            "method": "momo"
        }
    )
    client.post(
        "/payments",
        json={
            "order_id": order.id,
            "amount": "40.00",
            "verified_by": "staff_1",
            "method": "cash"
        }
    )

    # List payments for order
    response = client.get(f"/payments?order_id={order.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    amounts = [p["amount"] for p in data]
    assert "30.00" in amounts
    assert "40.00" in amounts


def test_list_all_payments(client: TestClient, setup_order):
    tenant, contact, order = setup_order

    # Create payment
    client.post(
        "/payments",
        json={
            "order_id": order.id,
            "amount": "25.00",
            "verified_by": "staff_1",
            "method": "momo"
        }
    )

    # List all payments
    response = client.get("/payments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
