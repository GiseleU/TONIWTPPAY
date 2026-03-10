# Tests for summary_service

import pytest
from sqlalchemy.orm import Session
from app.services.summary_service import generate_daily_summary
from app.models import DailySummary, Tenant, Order, Inquiry, Contact, WhatsAppAccount
from datetime import date


def test_generate_daily_summary_creates_new(db_session: Session):
    tenant = Tenant(id="T001", name="Test Tenant")
    contact = Contact(id="C001", tenant_id=tenant.id, name="Test", phone_number="123")
    wa = WhatsAppAccount(id="WA001", tenant_id=tenant.id, phone_number="456", phone_number_id="phone_wa001")
    db_session.add(tenant)
    db_session.add(contact)
    db_session.add(wa)
    summary_date = date.today()
    order = Order(
        id="O001",
        tenant_id=tenant.id,
        inquiry_id="I001",
        amount=100.0,
        customer_name="Test",
        customer_phone="123",
        created_at=summary_date
    )
    db_session.add(order)
    inquiry = Inquiry(
        id="I001",
        tenant_id=tenant.id,
        contact_id=contact.id,
        whatsapp_account_id=wa.id,
        message="Test message",
        status="confirmed",
        created_at=summary_date
    )
    db_session.add(inquiry)
    db_session.commit()

    summary = generate_daily_summary(db_session, tenant.id, summary_date)

    assert summary.tenant_id == tenant.id
    assert summary.summary_date == summary_date
    assert summary.total_orders == 1
    assert summary.total_inquiries == 1


def test_generate_daily_summary_updates_existing(db_session: Session):
    tenant = Tenant(id="T002", name="Test Tenant")
    db_session.add(tenant)
    summary_date = date.today()
    existing = DailySummary(
        id="DS001",
        tenant_id=tenant.id,
        summary_date=summary_date,
        total_orders=5
    )
    db_session.add(existing)
    db_session.commit()

    summary = generate_daily_summary(db_session, tenant.id, summary_date)

    assert summary.id == existing.id
    assert summary.total_orders == 0  # No orders, so updated to 0
