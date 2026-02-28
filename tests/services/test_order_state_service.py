# tests/services/test_order_state_service.py

import pytest
from sqlalchemy.orm import Session
from app.services.order_state_service import create_order_from_inquiry, OrderStateError
from app.models.inquiry import Inquiry
from app.models.order import Order
from app.models.contact import Contact
from app.models.whatsapp_account import WhatsAppAccount

@pytest.mark.parametrize("missing_field", ["name", "phone"])
def test_create_order_missing_customer_data(db_session: Session, missing_field: str):
    """
    Creating an order should fail if required customer data is missing.
    """
    whatsapp_account = WhatsAppAccount(id="WA123", tenant_id="tenant_1", phone_number="+1234567890")
    db_session.add(whatsapp_account)
    contact = Contact(id="C123", tenant_id="tenant_1", name="Alice", phone_number="0123456789")
    db_session.add(contact)
    db_session.commit()

    inquiry = Inquiry(
        id="T1234",
        tenant_id="tenant_1",
        whatsapp_account_id=whatsapp_account.id,
        message="Hello",
        status="confirmed",
        amount=100.0,
        contact_id=contact.id
    )
    db_session.add(inquiry)
    db_session.commit()

    kwargs = dict(
        inquiry_id=inquiry.id,
        tenant_id="tenant_1",
        customer_name="Alice",
        customer_phone="0123456789",
        customer_address="123 Street",
        db=db_session
    )

    # Remove the required field
    if missing_field == "name":
        kwargs["customer_name"] = ""
    else:
        kwargs["customer_phone"] = ""

    with pytest.raises(OrderStateError):
        create_order_from_inquiry(**kwargs)


def test_create_order_success(db_session: Session):
    """
    Confirmed inquiry with all required data creates an Order and updates inquiry status.
    """
    whatsapp_account = WhatsAppAccount(id="WA456", tenant_id="tenant_1", phone_number="+1234567891")
    db_session.add(whatsapp_account)
    contact = Contact(id="C456", tenant_id="tenant_1", name="Bob", phone_number="0987654321")
    db_session.add(contact)
    db_session.commit()

    inquiry = Inquiry(
        id="T5678",
        tenant_id="tenant_1",
        whatsapp_account_id=whatsapp_account.id,
        message="Hi",
        status="confirmed",
        amount=50.0,
        contact_id=contact.id
    )
    db_session.add(inquiry)
    db_session.commit()

    order = create_order_from_inquiry(
        inquiry_id=inquiry.id,
        tenant_id="tenant_1",
        customer_name="Bob",
        customer_phone="0987654321",
        customer_address="456 Avenue",
        db=db_session
    )

    # Validate order fields
    assert order.id.startswith("O")
    assert order.inquiry_id == inquiry.id
    assert order.tenant_id == "tenant_1"
    assert order.contact_id == contact.id
    assert order.customer_name == "Bob"
    assert order.customer_phone == "0987654321"
    assert order.customer_address == "456 Avenue"
    assert inquiry.status == "completed"


def test_create_order_duplicate_prevention(db_session: Session):
    """
    Attempting to create an order for an inquiry that already has an order fails.
    """
    whatsapp_account = WhatsAppAccount(id="WA789", tenant_id="tenant_1", phone_number="+1234567892")
    db_session.add(whatsapp_account)
    contact = Contact(id="C789", tenant_id="tenant_1", name="Carol", phone_number="111222333")
    db_session.add(contact)
    db_session.commit()

    inquiry = Inquiry(
        id="T9999",
        tenant_id="tenant_1",
        whatsapp_account_id=whatsapp_account.id,
        message="Order please",
        status="confirmed",
        amount=75.0,
        contact_id=contact.id
    )
    db_session.add(inquiry)
    db_session.commit()

    # First creation succeeds
    order1 = create_order_from_inquiry(
        inquiry_id=inquiry.id,
        tenant_id="tenant_1",
        customer_name="Carol",
        customer_phone="111222333",
        customer_address=None,
        db=db_session
    )
    assert order1.id.startswith("O")

    # Second creation should fail
    with pytest.raises(OrderStateError):
        create_order_from_inquiry(
            inquiry_id=inquiry.id,
            tenant_id="tenant_1",
            customer_name="Carol",
            customer_phone="111222333",
            customer_address=None,
            db=db_session
        )


def test_create_order_invalid_inquiry_status(db_session: Session):
    """
    Orders cannot be created from inquiries that are not 'confirmed'.
    """
    whatsapp_account = WhatsAppAccount(id="WA101", tenant_id="tenant_1", phone_number="+1234567893")
    db_session.add(whatsapp_account)
    contact = Contact(id="C101", tenant_id="tenant_1", name="Dave", phone_number="444555666")
    db_session.add(contact)
    db_session.commit()

    inquiry = Inquiry(
        id="T8888",
        tenant_id="tenant_1",
        whatsapp_account_id=whatsapp_account.id,
        message="Pending inquiry",
        status="pending",  # Not confirmed
        amount=120.0,
        contact_id=contact.id
    )
    db_session.add(inquiry)
    db_session.commit()

    with pytest.raises(OrderStateError):
        create_order_from_inquiry(
            inquiry_id=inquiry.id,
            tenant_id="tenant_1",
            customer_name="Dave",
            customer_phone="444555666",
            customer_address=None,
            db=db_session
        )