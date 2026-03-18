# app/integrations/whatsapp_client.py
"""
WhatsApp Cloud API client for ToniWtpPay MVP.

Supports:
- Sending text messages
- Sending interactive buttons (yes/no, add more)
- Sending interactive lists (product selection)
"""

import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings


class WhatsAppClient:
    """Async client for WhatsApp Cloud API."""

    def __init__(self):
        self.base_url = "https://graph.facebook.com"
        self.version = "v18.0"  # Can update if FB changes API
        self.access_token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", None)
        self.phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", None)

        if not self.access_token or not self.phone_number_id:
            raise RuntimeError(
                "WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID must be set in environment"
            )

        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send a simple text message."""
        url = f"{self.base_url}/{self.version}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"WhatsApp API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Unexpected error sending WhatsApp message: {e}")
            raise

    async def send_interactive_buttons(
        self, to: str, message: str, buttons: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Send interactive button message (e.g., Yes/No prompts)."""
        url = f"{self.base_url}/{self.version}/{self.phone_number_id}/messages"

        formatted_buttons = [
            {
                "type": "reply",
                "reply": {"id": b.get("id", ""), "title": b.get("title", "")[:20]},
            }
            for b in buttons
        ]

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": message},
                "action": {"buttons": formatted_buttons},
            },
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"WhatsApp API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Unexpected error sending interactive buttons: {e}")
            raise

    async def send_interactive_list(
        self,
        to: str,
        message: str,
        button_text: str = "Hitamo",
        sections: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send interactive list message (e.g., product selection)."""
        url = f"{self.base_url}/{self.version}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": message},
                "action": {"button": button_text, "sections": sections or []},
            },
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"WhatsApp API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Unexpected error sending interactive list: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global singleton instance
_whatsapp_client: Optional[WhatsAppClient] = None


def get_whatsapp_client() -> WhatsAppClient:
    """Get or create the global WhatsApp client instance."""
    global _whatsapp_client
    if _whatsapp_client is None:
        _whatsapp_client = WhatsAppClient()
    return _whatsapp_client