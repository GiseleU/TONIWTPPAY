# from pydantic import BaseModel, Field
# from typing import Optional, Dict, Any, List


# class WhatsAppMetadata(BaseModel):
#     display_phone_number: str
#     phone_number_id: str


# class WhatsAppMessageContent(BaseModel):
#     from_: str = Field(alias="from")
#     id: str
#     timestamp: str
#     type: str = "text"
#     text: Optional[Dict[str, str]] = None


# class WhatsAppChangeValue(BaseModel):
#     messaging_product: str = "whatsapp"
#     metadata: Optional[WhatsAppMetadata] = None
#     messages: Optional[List[WhatsAppMessageContent]] = None


# class WhatsAppChange(BaseModel):
#     value: Optional[WhatsAppChangeValue] = None
#     field: str = "messages"


# class WhatsAppEntry(BaseModel):
#     id: str
#     changes: List[WhatsAppChange] = []


# class MetaWhatsAppWebhook(BaseModel):
#     """Full Meta WhatsApp webhook payload format"""
#     object: str = "whatsapp_business_account"
#     entry: List[WhatsAppEntry] = []


# class WhatsappMessage(BaseModel):
#     """Simplified flat format for testing or direct API calls"""
#     message_id: str
#     to: str
#     from_: str = Field(alias="from")  # 'from' is a keyword, so use from_
#     text: str

#     class Config:
#         extra = "allow"  # Allow extra fields for flexibility


# def parse_whatsapp_payload(payload: dict) -> dict:
#     """
#     Parse WhatsApp payload from either format:
#     1. Flat format: {"message_id": "...", "to": "...", "from": "...", "text": "..."}
#     2. Meta format: {"object": "whatsapp_business_account", "entry": [...]}
    
#     Returns a standardized dict with: message_id, to, from, text
#     """
#     # Check if it's the Meta format (nested)
#     if "entry" in payload and payload.get("entry"):
#         entry = payload["entry"][0]
#         if entry and entry.get("changes"):
#             change_value = entry["changes"][0].get("value", {})
#             messages = change_value.get("messages", [])
            
#             if messages:
#                 msg = messages[0]
#                 metadata = change_value.get("metadata", {})
                
#                 return {
#                     "message_id": msg.get("id", ""),
#                     "to": metadata.get("display_phone_number", ""),
#                     "from": msg.get("from", ""),
#                     "text": msg.get("text", {}).get("body", "") if msg.get("text") else "",
#                     # Keep original payload for reference
#                     "_original": payload
#                 }
    
#     # Flat format - return as-is
#     return {
#         "message_id": payload.get("message_id", ""),
#         "to": payload.get("to", ""),
#         "from": payload.get("from", ""),
#         "text": payload.get("text", ""),
#         "_original": payload
#     }


# class MomoWebhook(BaseModel):
#     transaction_id: str
#     tenant_id: str
#     # Add other fields as needed based on MoMo API
#     amount: Optional[float] = None
#     status: Optional[str] = None
#     payload: Optional[Dict[str, Any]] = None





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

    # -----------------------
    # Meta nested format
    # -----------------------
    if "entry" in payload and payload.get("entry"):

        entry = payload["entry"][0]

        if entry and entry.get("changes"):

            change_value = entry["changes"][0].get("value", {})
            messages = change_value.get("messages", [])

            if messages:

                msg = messages[0]
                metadata = change_value.get("metadata", {})

                return {
                    "message_id": msg.get("id", ""),
                    "phone_number_id": metadata.get("phone_number_id"),
                    "to": metadata.get("display_phone_number", ""),
                    "from": msg.get("from", ""),
                    "text": msg.get("text", {}).get("body", "") if msg.get("text") else "",
                    "_original": payload,
                }

    # -----------------------
    # Flat test format
    # -----------------------
    return {
        "message_id": payload.get("message_id", ""),
        "phone_number_id": payload.get("phone_number_id"),
        "to": payload.get("to", ""),
        "from": payload.get("from", ""),
        "text": payload.get("text", ""),
        "_original": payload,
    }


class MomoWebhook(BaseModel):
    transaction_id: str
    tenant_id: str
    amount: Optional[float] = None
    status: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None