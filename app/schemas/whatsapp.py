from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


# -----------------------
# Nested models for Meta payload
# -----------------------
class WhatsAppMetadata(BaseModel):
    display_phone_number: Optional[str] = None
    phone_number_id: Optional[str] = None


class WhatsAppContactProfile(BaseModel):
    name: str


class WhatsAppContact(BaseModel):
    profile: WhatsAppContactProfile
    wa_id: str


class WhatsAppMessageContent(BaseModel):
    from_: str = Field(alias="from")
    id: str
    timestamp: str
    type: str = "text"
    text: Optional[Dict[str, str]] = None


class WhatsAppChangeValue(BaseModel):
    messaging_product: str = "whatsapp"
    metadata: Optional[WhatsAppMetadata] = None
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[WhatsAppMessageContent]] = None


class WhatsAppChange(BaseModel):
    value: Optional[WhatsAppChangeValue] = None
    field: str = "messages"


class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChange] = []


class MetaWhatsAppWebhook(BaseModel):
    object: str = "whatsapp_business_account"
    entry: List[WhatsAppEntry] = []


# -----------------------
# Flattened message for service
# -----------------------
class WhatsappMessage(BaseModel):
    message_id: str
    to: Optional[str] = None
    from_: str = Field(alias="from")
    name: Optional[str] = None
    text: str

    class Config:
        extra = "allow"


# -----------------------
# Payload parser
# -----------------------
def parse_whatsapp_payload(payload: dict) -> dict:
    """
    Parse Meta WhatsApp webhook payload into a simplified dict:
    {
        'message_id': str,
        'to': str,
        'from': str,
        'name': str,
        'text': str,
        '_original': dict
    }
    """

    # Check if payload uses Meta nested format
    entries = payload.get("entry", [])
    if entries:
        entry = entries[0]
        changes = entry.get("changes", [])
        if changes:
            change_value = changes[0].get("value", {})

            # Handle status updates (delivery receipts)
            statuses = change_value.get("statuses", [])
            if statuses:
                print(f"📨 Status update: {statuses[0].get('status', 'unknown')} for message {statuses[0].get('id')}")
                return {
                    "type": "status",
                    "status": statuses[0].get("status"),
                    "message_id": statuses[0].get("id"),
                    "_original": payload,
                }

            # Handle incoming messages
            messages = change_value.get("messages", [])
            contacts = change_value.get("contacts", [])

            if messages and contacts:
                msg = messages[0]
                contact = contacts[0]

                return {
                    "message_id": msg.get("id", ""),
                    "to": change_value.get("metadata", {}).get("display_phone_number"),
                    "from": msg.get("from"),
                    "name": contact.get("profile", {}).get("name"),
                    "text": msg.get("text", {}).get("body", "") if msg.get("text") else "",
                    "_original": payload,
                }

    # Fallback: flat test format
    from_phone = payload.get("from", "")
    text_body = payload.get("text", "")
    name = payload.get("name", None)

    if from_phone and text_body:
        return {
            "message_id": payload.get("message_id", ""),
            "to": payload.get("to", None),
            "from": from_phone,
            "name": name,
            "text": text_body,
            "_original": payload,
        }

    # If we reach here, it's a valid webhook we don't process (status, etc.)
    print(f"ℹ️ Acknowledged webhook (no action needed): {payload.get('object')}")
    return {"type": "acknowledged", "_original": payload}
