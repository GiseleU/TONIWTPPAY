from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class WhatsAppMetadata(BaseModel):
    display_phone_number: str
    phone_number_id: str


class WhatsAppMessageContent(BaseModel):
    from_: str = Field(alias="from")
    id: str
    timestamp: str
    type: str = "text"
    text: Optional[Dict[str, str]] = None


class WhatsAppChangeValue(BaseModel):
    messaging_product: str = "whatsapp"
    metadata: Optional[WhatsAppMetadata] = None
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


class WhatsappMessage(BaseModel):
    message_id: str
    phone_number_id: Optional[str] = None
    to: str
    from_: str = Field(alias="from")
    text: str

    class Config:
        extra = "allow"


def parse_whatsapp_payload(payload: dict) -> dict:
    """
    Parse Meta WhatsApp webhook payload into standardized format.
    """

    # Early validation for completely invalid payloads
    has_entry = "entry" in payload and payload.get("entry")
    has_from = "from" in payload
    has_text = "text" in payload
    
    if not has_entry and not (has_from and has_text):
        raise KeyError("Invalid payload structure")

    # -----------------------
    # Meta nested format
    # -----------------------
    if has_entry:

        entry = payload["entry"][0]

        if entry and entry.get("changes"):

            change_value = entry["changes"][0].get("value", {})
            messages = change_value.get("messages", [])

            if messages:

                msg = messages[0]
                metadata = change_value.get("metadata", {})

                from_phone = msg.get("from", "")
                text_body = msg.get("text", {}).get("body", "") if msg.get("text") else ""
                
                if from_phone and text_body:
                    return {
                        "message_id": msg.get("id", ""),
                        "phone_number_id": metadata.get("phone_number_id"),
                        "to": metadata.get("display_phone_number", ""),
                        "from": from_phone,
                        "text": text_body,
                        "_original": payload,
                    }

    # -----------------------
    # Flat test format
    # -----------------------
    from_phone = payload.get("from", "")
    text_body = payload.get("text", "")
    
    if from_phone and text_body:
        return {
            "message_id": payload.get("message_id", ""),
            "phone_number_id": payload.get("phone_number_id"),
            "to": payload.get("to", ""),
            "from": from_phone,
            "text": text_body,
            "_original": payload,
        }
    
    raise KeyError("Invalid payload structure")


# class MomoWebhook(BaseModel):
#     transaction_id: str
#     tenant_id: str
#     amount: Optional[float] = None
#     status: Optional[str] = None
#     payload: Optional[Dict[str, Any]] = None