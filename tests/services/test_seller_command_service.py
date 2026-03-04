# tests/services/test_seller_command_service.py
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from app.services.seller_command_service import (
    parse_seller_command,
    execute_seller_command,
    CommandError,
)
from app.core.enums import EventType, ActorType, WorkflowState
from app.models.workflow_session import WorkflowSession
from app.models.inquiry import Inquiry


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
def seller_phone():
    return "+250788123456"


@pytest.fixture
def inquiry_mock(tenant_id):
    """A fresh inquiry in 'new' status"""
    inquiry = MagicMock()
    inquiry.id = "I1001"
    inquiry.status = "new"
    inquiry.tenant_id = tenant_id
    inquiry.amount = None
    return inquiry


@pytest.fixture
def workflow_session_mock(inquiry_mock, tenant_id):
    """A workflow session in AWAITING_CONFIRM state"""
    session = MagicMock()
    session.id = "WS123"
    session.seller_phone = "+250788123456"
    session.inquiry_id = inquiry_mock.id
    session.workflow_state = WorkflowState.AWAITING_CONFIRM
    session.order_id = None
    return session


# ---------------------
# Parsing Tests (Phase 2 - Simplified Commands)
# ---------------------
def test_parse_confirm_command():
    """CONFIRM - Start workflow on latest 'new' inquiry (no ID required)"""
    c1 = parse_seller_command("CONFIRM")
    assert c1["action"] == "confirm"


def test_parse_paid_command():
    """PAID - Record payment on active session"""
    c2 = parse_seller_command("PAID")
    assert c2["action"] == "paid"


def test_parse_yes_command():
    """YES - Confirm order summary"""
    c3 = parse_seller_command("YES")
    assert c3["action"] == "yes"


def test_parse_no_command():
    """NO - Restart/cancel workflow"""
    c4 = parse_seller_command("NO")
    assert c4["action"] == "no"


def test_parse_done_command():
    """DONE - Finish product entry"""
    c5 = parse_seller_command("DONE")
    assert c5["action"] == "done"


def test_parse_product_entry():
    """Product entry pattern: 'Product Name Quantity Price'"""
    c6 = parse_seller_command("Juice 2 800")
    assert c6["action"] == "add_product"
    assert c6["product_name"] == "JUICE"  # Parser uses .upper()
    assert c6["quantity"] == 2
    assert c6["price"] == 800


def test_parse_summary_command():
    c7 = parse_seller_command("SUMMARY")
    assert c7["action"] == "summary"


def test_parse_invalid_command():
    with pytest.raises(CommandError):
        parse_seller_command("INVALID T123")


# ---------------------
# Command Execution Tests (Phase 2)
# ---------------------
def test_execute_confirm_command(db_mock, seller_id, tenant_id, seller_phone, inquiry_mock):
    """Test CONFIRM command creates workflow session"""
    # Query counter to track call order
    query_count = [0]
    
    def query_side_effect(*args):
        query_count[0] += 1
        mock_result = MagicMock()
        
        # First query: get_latest_new_inquiry - db.query(Inquiry).filter(...)
        if query_count[0] == 1:
            mock_result.filter.return_value.order_by.return_value.first.return_value = inquiry_mock
        # Second query: get_active_workflow_session - db.query(WorkflowSession).filter(...)
        # Third query: nested db.query(Inquiry.id).filter(...) inside get_active_workflow_session
        else:
            # Return None for no existing session
            mock_result.filter.return_value.order_by.return_value.first.return_value = None
            
        return mock_result
    
    db_mock.query.side_effect = query_side_effect

    result = execute_seller_command("CONFIRM", seller_id, tenant_id, db_mock, seller_phone)
    
    assert result["status"] == "ok"
    assert result["action"] == "workflow_started"
    assert inquiry_mock.status == "confirmed"
    assert db_mock.add.called
    assert db_mock.commit.called


def test_execute_paid_command(db_mock, seller_id, tenant_id, seller_phone, workflow_session_mock):
    """Test PAID command records payment"""
    # Mock: active workflow session in AWAITING_PAYMENT state
    workflow_session_mock.workflow_state = WorkflowState.AWAITING_PAYMENT
    workflow_session_mock.order_id = "O123"
    workflow_session_mock.order = MagicMock()
    workflow_session_mock.order.status = "pending"
    
    db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = workflow_session_mock

    result = execute_seller_command("PAID", seller_id, tenant_id, db_mock, seller_phone)
    
    assert result["status"] == "ok"
    assert result["action"] == "payment_recorded"
    assert workflow_session_mock.workflow_state == WorkflowState.COMPLETED
    assert workflow_session_mock.order.status == "paid"


def test_execute_yes_command(db_mock, seller_id, tenant_id, seller_phone, workflow_session_mock):
    """Test YES command confirms order summary"""
    # Mock: active workflow session in ORDER_SUMMARY state
    workflow_session_mock.workflow_state = WorkflowState.ORDER_SUMMARY
    workflow_session_mock.order_id = "O123"
    
    db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = workflow_session_mock

    result = execute_seller_command("YES", seller_id, tenant_id, db_mock, seller_phone)
    
    assert result["status"] == "ok"
    assert result["action"] == "order_confirmed"
    assert workflow_session_mock.workflow_state == WorkflowState.AWAITING_PAYMENT


def test_execute_no_command(db_mock, seller_id, tenant_id, seller_phone, workflow_session_mock):
    """Test NO command cancels workflow"""
    db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = workflow_session_mock

    result = execute_seller_command("NO", seller_id, tenant_id, db_mock, seller_phone)
    
    assert result["status"] == "ok"
    assert result["action"] == "workflow_cancelled"
    assert workflow_session_mock.workflow_state == WorkflowState.CANCELLED


def test_summary_command(db_mock, seller_id, tenant_id):
    """Test SUMMARY command returns daily summary"""
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
def test_illegal_transition_raises(db_mock, seller_id, tenant_id, seller_phone, inquiry_mock):
    """Test that illegal workflow transitions raise errors"""
    # Mock: existing workflow session in COMPLETED state
    session = MagicMock()
    session.workflow_state = WorkflowState.COMPLETED
    db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = session

    # Cannot transition from COMPLETED to ENTERING_PRODUCTS
    with pytest.raises(Exception):
        execute_seller_command("CONFIRM", seller_id, tenant_id, db_mock, seller_phone)


def test_paid_command_wrong_state(db_mock, seller_id, tenant_id, seller_phone, workflow_session_mock):
    """Test PAID command fails if not in AWAITING_PAYMENT state"""
    workflow_session_mock.workflow_state = WorkflowState.ENTERING_PRODUCTS
    
    db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = workflow_session_mock

    with pytest.raises(CommandError):
        execute_seller_command("PAID", seller_id, tenant_id, db_mock, seller_phone)


# ---------------------
# No Active Session Tests
# ---------------------
def test_confirm_no_inquiry_raises(db_mock, seller_id, tenant_id, seller_phone):
    """Test CONFIRM raises error when no 'new' inquiry exists"""
    db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    with pytest.raises(CommandError):
        execute_seller_command("CONFIRM", seller_id, tenant_id, db_mock, seller_phone)


def test_paid_no_session_raises(db_mock, seller_id, tenant_id, seller_phone):
    """Test PAID raises error when no active session exists"""
    db_mock.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    with pytest.raises(CommandError):
        execute_seller_command("PAID", seller_id, tenant_id, db_mock, seller_phone)
