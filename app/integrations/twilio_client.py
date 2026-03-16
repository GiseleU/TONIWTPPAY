# Twilio WhatsApp client for sending messages (MVP - text only, interactive stubbed)

import asyncio
from typing import Optional, Dict, Any, List
from twilio.rest import Client as TwilioClient
from app.core.config import settings


class WhatsAppClient:
    """
    Twilio WhatsApp client matching Meta interface for minimal migration.
    Supports text messages. Interactive → text fallback (Content API later).
    """

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.whatsapp_number = settings.TWILIO_WHATSAPP_NUMBER

        if not all([self.account_sid, self.auth_token, self.whatsapp_number]):
            raise RuntimeError("TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER must be configured")

        self.client = TwilioClient(self.account_sid, self.auth_token)

    def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send text message (sync Twilio API).
        """
        msg = self.client.messages.create(
            from_=f"whatsapp:{self.whatsapp_number}",
            to=f"whatsapp:{to}",
            body=message
        )
        return {"messages": [{"id": msg.sid}]}

    def send_interactive_buttons(self, to: str, message: str, buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        MVP: Fallback to text (buttons disabled). Use Twilio Content API later.
        """
        button_text = " | ".join(b["title"] for b in buttons[:3])
        fallback = f"{message}\n{button_text}\n(Reply: yes/no)"
        return self.send_message(to, fallback)

    def send_interactive_list(self, to: str, message: str, button_text: str = "Hitamo", sections: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        MVP: Fallback to text list. Use Twilio Content API later.
        """
        fallback = f"{message}\n{button_text}\n(List coming soon - reply product name)"
        return self.send_message(to, fallback)

    def close(self):
        pass  # Twilio Client stateless


# Global singleton
_whatsapp_client: Optional[WhatsAppClient] = None


def get_whatsapp_client() -> WhatsAppClient:
    global _whatsapp_client
    if _whatsapp_client is None:
        _whatsapp_client = WhatsAppClient()
    return _whatsapp_client
