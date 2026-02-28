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
