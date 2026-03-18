# tests/schemas/test_webhook.py

import pytest
from app.schemas import whatsapp
from datetime import datetime


def test_whatsapp_metadata_model():
    meta = whatsapp.WhatsAppMetadata(display_phone_number="+250700000001", phone_number_id="wa_test_001")
    assert meta.display_phone_number == "+250700000001"
    assert meta.phone_number_id == "wa_test_001"


def test_whatsapp_message_content_model():
    msg_data = {
        "from": "250700000001",
        "id": "MSG001",
        "timestamp": "2026-03-18T11:00:00",
        "type": "text",
        "text": {"body": "Hello"}
    }
    msg = whatsapp.WhatsAppMessageContent(**msg_data)
    assert msg.from_ == "250700000001"
    assert msg.id == "MSG001"
    assert msg.text["body"] == "Hello"


def test_meta_whatsapp_webhook_model():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "entry_001",
                "changes": [
                    {"field": "messages", "value": {"messaging_product": "whatsapp"}}
                ]
            }
        ]
    }
    meta_webhook = whatsapp.MetaWhatsAppWebhook(**payload)
    assert meta_webhook.object == "whatsapp_business_account"
    assert len(meta_webhook.entry) == 1
    assert meta_webhook.entry[0].id == "entry_001"


def test_parse_whatsapp_payload_nested():
    payload = {
        "entry": [
            {
                "id": "entry_001",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+250700000001",
                                "phone_number_id": "wa_test_001"
                            },
                            "messages": [
                                {
                                    "from": "250700000002",
                                    "id": "MSG001",
                                    "timestamp": "2026-03-18T11:00:00",
                                    "type": "text",
                                    "text": {"body": "Hello"}
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    parsed = whatsapp.parse_whatsapp_payload(payload)
    assert parsed["message_id"] == "MSG001"
    assert parsed["from"] == "250700000002"
    assert parsed["to"] == "+250700000001"
    assert parsed["text"] == "Hello"
    assert "_original" in parsed


def test_parse_whatsapp_payload_flat():
    payload = {
        "message_id": "MSG002",
        "phone_number_id": "wa_test_002",
        "to": "+250700000003",
        "from": "250700000004",
        "text": "Hi"
    }

    parsed = whatsapp.parse_whatsapp_payload(payload)
    assert parsed["message_id"] == "MSG002"
    assert parsed["from"] == "250700000004"
    assert parsed["to"] == "+250700000003"
    assert parsed["text"] == "Hi"
    assert parsed["_original"] == payload


# def test_momo_webhook_model():
#     momo_data = {
#         "transaction_id": "TX001",
#         "tenant_id": "T001",
#         "amount": 2500.0,
#         "status": "success",
#         "payload": {"raw": "data"}
#     }
#     momo = whatsapp.MomoWebhook(**momo_data)
#     assert momo.transaction_id == "TX001"
#     assert momo.amount == 2500.0
#     assert momo.status == "success"
#     assert momo.payload["raw"] == "data"