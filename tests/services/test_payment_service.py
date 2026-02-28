# tests/services/test_payment_service.py

import pytest
from sqlalchemy.orm import Session
from decimal import Decimal
from app.services.payment_service import record_manual_payment, PaymentError
from app.models.order import Order
from app.models.contact import Contact
from app.models.tenant import Tenant
from app.models.whatsapp_account import WhatsAppAccount
from app.models.event import Event
from app.core.enums import CoexistenceStatus, EventType

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
        status="completed"  # Set to completed for payment recording
    )
    db_session.add(order)
    db_session.commit()
    return db_session, tenant, contact, order


def test_record_manual_payment_success(setup_order):
    db_session, tenant, contact, order = setup_order

    payment = record_manual_payment(
        order_id=order.id,
        amount=Decimal("100.00"),
        verified_by="staff_1",
        method="momo",
        db=db_session,
    )

    assert payment.id.startswith("P")
    assert payment.order_id == order.id
    assert payment.amount == Decimal("100.00")
    assert payment.verified_by == "staff_1"
    assert payment.method == "momo"

    # Ensure order status updated to paid
    db_session.refresh(order)
    assert order.status == "paid"

    # Ensure event created
    event = db_session.query(Event).filter(Event.payment_id == payment.id).first()
    assert event.event_type == EventType.PAYMENT_RECORDED
    assert order.id == event.order_id


def test_record_duplicate_payment_fails(setup_order):
    db_session, tenant, contact, order = setup_order

    # First payment
    record_manual_payment(
        order_id=order.id,
        amount=Decimal("50.00"),
        verified_by="staff_1",
        method="momo",
        db=db_session,
    )

    # Attempt duplicate same amount
    with pytest.raises(PaymentError) as exc:
        record_manual_payment(
            order_id=order.id,
            amount=Decimal("50.00"),
            verified_by="staff_1",
            method="momo",
            db=db_session,
        )
    assert "Duplicate payment" in str(exc.value)


def test_record_overpayment_fails(setup_order):
    db_session, tenant, contact, order = setup_order

    # First payment
    record_manual_payment(
        order_id=order.id,
        amount=Decimal("60.00"),
        verified_by="staff_1",
        method="momo",
        db=db_session,
    )

    # Attempt overpayment
    with pytest.raises(PaymentError) as exc:
        record_manual_payment(
            order_id=order.id,
            amount=Decimal("50.00"),
            verified_by="staff_1",
            method="momo",
            db=db_session,
        )
    assert "would exceed order total" in str(exc.value)


def test_record_payment_invalid_order_status(setup_order):
    db_session, tenant, contact, order = setup_order

    # Change order status to pending
    order.status = "pending"
    db_session.add(order)
    db_session.commit()

    with pytest.raises(PaymentError) as exc:
        record_manual_payment(
            order_id=order.id,
            amount=Decimal("100.00"),
            verified_by="staff_1",
            method="momo",
            db=db_session,
        )
    assert "must be in 'completed' status" in str(exc.value)


def test_record_payment_nonexistent_order(db_session):
    with pytest.raises(PaymentError) as exc:
        record_manual_payment(
            order_id="O9999",
            amount=Decimal("100.00"),
            verified_by="staff_1",
            method="momo",
            db=db_session,
        )
    assert "Order O9999 not found" in str(exc.value)


def test_payment_event_payload(setup_order):
    db_session, tenant, contact, order = setup_order

    payment = record_manual_payment(
        order_id=order.id,
        amount=Decimal("75.00"),
        verified_by="staff_1",
        method="cash",
        notes="Partial payment",
        db=db_session,
    )

    event = db_session.query(Event).filter(Event.payment_id == payment.id).first()
    assert event.payload["method"] == "cash"
    assert event.payload["notes"] == "Partial payment"
    assert "recorded for order" in event.payload["message"]


def test_partial_payment_does_not_mark_paid(setup_order):
    db_session, tenant, contact, order = setup_order

    record_manual_payment(
        order_id=order.id,
        amount=Decimal("50.00"),
        verified_by="staff_1",
        method="momo",
        db=db_session,
    )

    # Order should still be completed, not paid
    db_session.refresh(order)
    assert order.status == "completed"
    assert not order.is_fully_paid()
