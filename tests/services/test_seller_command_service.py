# tests/services/test_seller_command_service.py
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from app.services.seller_command_service import (
    parse_seller_command,
    execute_seller_command,
    CommandError,
)
from app.core.enums import EventType, ActorType

@pytest.fixture
def db_mock():
    """Mocked SQLAlchemy session"""
    return MagicMock(spec=Session)

@pytest.fixture
def tenant_id():
    return "tenant-123"

@pytest.fixture
def seller_id():
    return "seller-001"

@pytest.fixture
def inquiry_mock(tenant_id):
    """A fresh inquiry in 'new' status"""
    inquiry = MagicMock()
    inquiry.id = "T1001"
    inquiry.status = "new"
    inquiry.tenant_id = tenant_id
    inquiry.amount = None
    return inquiry


# ---------------------
# Parsing Tests
# ---------------------
def test_parse_valid_commands():
    c1 = parse_seller_command("CONFIRM T1001 500")
    assert c1["action"] == "confirm"
    assert c1["inquiry_id"] == "T1001"
    assert c1["amount"] == 500

    c2 = parse_seller_command("DROP T1002")
    assert c2["action"] == "drop"
    assert c2["inquiry_id"] == "T1002"

    c3 = parse_seller_command("SUMMARY")
    assert c3["action"] == "summary"

def test_parse_invalid_command():
    with pytest.raises(CommandError):
        parse_seller_command("INVALID T123")
    with pytest.raises(CommandError):
        parse_seller_command("CONFIRM T1001")  # Missing amount


# ---------------------
# Command Execution Tests
# ---------------------
def test_execute_confirm_command(db_mock, seller_id, tenant_id, inquiry_mock):
    db_mock.query().filter_by().first.return_value = inquiry_mock

    result = execute_seller_command("CONFIRM T1001 500", seller_id, tenant_id, db_mock)
    assert result["new_status"] == "confirmed"
    assert inquiry_mock.amount == 500
    assert db_mock.add.called  # inquiry event added
    assert db_mock.commit.called

def test_execute_drop_command(db_mock, seller_id, tenant_id, inquiry_mock):
    db_mock.query().filter_by().first.return_value = inquiry_mock

    result = execute_seller_command("DROP T1001", seller_id, tenant_id, db_mock)
    assert result["new_status"] == "dropped"
    assert db_mock.add.called
    assert db_mock.commit.called

def test_summary_command(db_mock, seller_id, tenant_id):
    # Mock the summary object
    summary_mock = MagicMock()
    summary_mock.total_orders = 5
    summary_mock.total_revenue = 1000.0
    summary_mock.paid_orders = 3
    summary_mock.paid_revenue = 750.0
    summary_mock.total_inquiries = 10
    summary_mock.confirmed_inquiries = 7
    summary_mock.dropped_inquiries = 2
    summary_mock.opt_outs = 1
    summary_mock.blocked_sends = 0
    summary_mock.failed_sends = 1
    summary_mock.quality_warnings = 0

    # Mock generate_daily_summary to return the summary
    from app.services import seller_command_service
    original_generate = seller_command_service.generate_daily_summary
    seller_command_service.generate_daily_summary = MagicMock(return_value=summary_mock)

    try:
        result = execute_seller_command("SUMMARY", seller_id, tenant_id, db_mock)
        assert result["status"] == "ok"
        assert "summary" in result
        summary = result["summary"]
        assert summary["total_orders"] == 5
        assert summary["total_revenue"] == 1000.0
        assert summary["paid_orders"] == 3
        assert summary["paid_revenue"] == 750.0
        assert summary["total_inquiries"] == 10
        assert summary["confirmed_inquiries"] == 7
        assert summary["dropped_inquiries"] == 2
        assert summary["opt_outs"] == 1
        assert summary["blocked_sends"] == 0
        assert summary["failed_sends"] == 1
        assert summary["quality_warnings"] == 0
    finally:
        seller_command_service.generate_daily_summary = original_generate


# ---------------------
# Illegal Transitions
# ---------------------
def test_illegal_transition_raises(db_mock, seller_id, tenant_id, inquiry_mock):
    # Move inquiry to confirmed first
    inquiry_mock.status = "confirmed"
    db_mock.query().filter_by().first.return_value = inquiry_mock

    # Cannot confirm again
    with pytest.raises(CommandError):
        execute_seller_command("CONFIRM T1001 500", seller_id, tenant_id, db_mock)

    # Cannot drop a completed inquiry
    inquiry_mock.status = "completed"
    with pytest.raises(CommandError):
        execute_seller_command("DROP T1001", seller_id, tenant_id, db_mock)


# ---------------------
# Cross-tenant Access
# ---------------------
def test_cross_tenant_access_raises(db_mock, seller_id, inquiry_mock):
    # Inquiry belongs to a different tenant
    inquiry_mock.tenant_id = "tenant-999"
    db_mock.query().filter_by().first.return_value = None

    with pytest.raises(CommandError):
        execute_seller_command("CONFIRM T1001 500", seller_id, "tenant-123", db_mock)


# ---------------------
# Event Recording Verification
# ---------------------
def test_event_recording_on_confirm(db_mock, seller_id, tenant_id, inquiry_mock):
    db_mock.query().filter_by().first.return_value = inquiry_mock

    execute_seller_command("CONFIRM T1001 500", seller_id, tenant_id, db_mock)
    added_event = db_mock.add.call_args[0][0]
    assert added_event.actor == ActorType.SELLER
    assert added_event.payload["command"] == "CONFIRM T1001 500"
    assert added_event.payload["seller_id"] == seller_id
    assert added_event.payload["new_status"] == "confirmed"

def test_event_recording_on_drop(db_mock, seller_id, tenant_id, inquiry_mock):
    db_mock.query().filter_by().first.return_value = inquiry_mock

    execute_seller_command("DROP T1001", seller_id, tenant_id, db_mock)
    added_event = db_mock.add.call_args[0][0]
    assert added_event.actor == ActorType.SELLER
    assert added_event.payload["command"] == "DROP T1001"
    assert added_event.payload["seller_id"] == seller_id
    assert added_event.payload["new_status"] == "dropped"
