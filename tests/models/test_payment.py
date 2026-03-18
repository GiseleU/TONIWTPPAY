# tests/models/test_payment.py

import uuid
from decimal import Decimal
from app.db.models_import import Payment, Tenant, Transaction


def test_create_payment(db_session):
    """Test creating a payment linked to a tenant and transaction."""

    # ---- Create Tenant ----
    tenant = Tenant(id=str(uuid.uuid4()), name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    # ---- Create Transaction ----
    transaction = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000001"
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    # ---- Create Payment ----
    payment_id = str(uuid.uuid4())
    payment = Payment(
        id=payment_id,
        tenant_id=tenant.id,
        transaction_id=transaction.id,
        amount=Decimal("5000.00"),
        method="momo",
        verified_by="seller_1",
        notes="Paid via MTN MoMo"
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)

    # ---- Assertions ----
    assert payment.id == payment_id
    assert payment.amount == Decimal("5000.00")
    assert payment.method == "momo"
    assert payment.verified_by == "seller_1"
    assert payment.notes == "Paid via MTN MoMo"

    # Relationships
    assert payment.tenant.id == tenant.id
    assert payment.transaction.id == transaction.id

    # Timestamp auto-generated
    assert payment.timestamp is not None


def test_payment_optional_fields(db_session):
    """Test creating a payment without optional fields."""

    tenant = Tenant(id=str(uuid.uuid4()), name="Tenant Optional")
    db_session.add(tenant)
    db_session.commit()

    transaction = Transaction(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        seller_phone="250700000002"
    )
    db_session.add(transaction)
    db_session.commit()

    payment = Payment(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        transaction_id=transaction.id,
        amount=Decimal("2000.00"),
        method="cash"
        # verified_by and notes omitted
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)

    # Assertions
    assert payment.amount == Decimal("2000.00")
    assert payment.method == "cash"
    assert payment.verified_by is None
    assert payment.notes is None