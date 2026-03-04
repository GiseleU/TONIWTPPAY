# WhatsApp Business API client for sending messages

import httpx
import json
from typing import Optional, Dict, Any
from app.core.config import settings


class WhatsAppClient:
    """
    WhatsApp Business API client for sending messages.

    Uses WhatsApp Cloud API for sending outbound messages.
    """

    def __init__(self):
        # WhatsApp Business API configuration
        self.base_url = "https://graph.facebook.com/v18.0"
        self.version = "v18.0"

        # Load from environment variables (to be added to config)
        self.access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
        self.phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)

        if not self.access_token or not self.phone_number_id:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID must be configured")

        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send a text message to a WhatsApp number.

        Args:
            to: Recipient phone number in international format (e.g., "250700000001")
            message: Text message to send

        Returns:
            WhatsApp API response

        Raises:
            HTTPException: If message sending fails
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            return result

        except httpx.HTTPStatusError as e:
            # Log the error and re-raise
            print(f"WhatsApp API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Unexpected error sending WhatsApp message: {e}")
            raise

    async def send_interactive_buttons(
        self,
        to: str,
        message: str,
        buttons: list[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Send an interactive message with buttons.

        Args:
            to: Recipient phone number in international format
            message: Text message to display
            buttons: List of button objects with 'id' and 'title' keys
                     e.g., [{"id": "yes", "title": "Yego"}, {"id": "no", "title": "Oya"}]

        Returns:
            WhatsApp API response

        Raises:
            HTTPException: If message sending fails
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"

        # Format buttons for WhatsApp API
        formatted_buttons = []
        for button in buttons:
            formatted_buttons.append({
                "type": "reply",
                "reply": {
                    "id": button.get("id", ""),
                    "title": button.get("title", "")[:20]  # WhatsApp limits title to 20 chars
                }
            })

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": message
                },
                "action": {
                    "buttons": formatted_buttons
                }
            }
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
        sections: list[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an interactive list message (for product selection).

        Args:
            to: Recipient phone number in international format
            message: Header/description text
            button_text: Text for the main button (default: "Hitamo")
            sections: List of section objects for the list
                     e.g: [{
                         "title": "Products",
                         "rows": [
                             {"id": "product_1", "title": "Juice", "description": "800 RWF"},
                             {"id": "product_2", "title": "Water", "description": "500 RWF"}
                         ]
                     }]

        Returns:
            WhatsApp API response

        Raises:
            HTTPException: If message sending fails
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": message
                },
                "action": {
                    "button": button_text,
                    "sections": sections or []
                }
            }
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


# Global client instance (create once, reuse)
_whatsapp_client: Optional[WhatsAppClient] = None


def get_whatsapp_client() -> WhatsAppClient:
    """Get or create the global WhatsApp client instance."""
    global _whatsapp_client
    if _whatsapp_client is None:
        _whatsapp_client = WhatsAppClient()
    return _whatsapp_client
