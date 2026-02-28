import pytest
from pydantic import ValidationError
from app.schemas.webhook import WhatsappMessage, MomoWebhook


def test_whatsapp_message_valid():
    """Test valid WhatsappMessage instantiation with alias"""
    data = {
        "message_id": "msg-123",
        "from": "+1234567890",  # Using 'from' key due to alias
        "to": "+0987654321",
        "text": "Hello world"
    }
    msg = WhatsappMessage(**data)
    assert msg.message_id == "msg-123"
    assert msg.from_ == "+1234567890"
    assert msg.to == "+0987654321"
    assert msg.text == "Hello world"


def test_whatsapp_message_missing_required():
    """Test WhatsappMessage validation error for missing required fields"""
    with pytest.raises(ValidationError):
        WhatsappMessage(message_id="msg-123", **{"from": "+1234567890"})  # Missing to, text


def test_whatsapp_message_model_dump_alias():
    """Test WhatsappMessage model_dump with alias"""
    msg = WhatsappMessage(
        message_id="msg-123",
        **{"from": "+1234567890"},
        to="+0987654321",
        text="Test message"
    )
    dumped = msg.model_dump(by_alias=True)
    assert "from" in dumped
    assert dumped["from"] == "+1234567890"
    assert "from_" not in dumped


def test_momo_webhook_valid():
    """Test valid MomoWebhook instantiation"""
    data = {
        "transaction_id": "txn-123",
        "tenant_id": "tenant-456",
        "amount": 100.50,
        "status": "completed",
        "payload": {"key": "value"}
    }
    webhook = MomoWebhook(**data)
    assert webhook.transaction_id == "txn-123"
    assert webhook.tenant_id == "tenant-456"
    assert webhook.amount == 100.50
    assert webhook.status == "completed"
    assert webhook.payload == {"key": "value"}


def test_momo_webhook_minimal():
    """Test MomoWebhook with minimal required fields"""
    data = {
        "transaction_id": "txn-123",
        "tenant_id": "tenant-456"
    }
    webhook = MomoWebhook(**data)
    assert webhook.amount is None
    assert webhook.status is None
    assert webhook.payload is None


def test_momo_webhook_missing_required():
    """Test MomoWebhook validation error for missing required fields"""
    with pytest.raises(ValidationError):
        MomoWebhook(transaction_id="txn-123")  # Missing tenant_id
