"""
Send WhatsApp responses/alerts.

This service handles outbound WhatsApp messaging for:
- Customer responses to inquiries
- Seller command confirmations
- System notifications
- Automated messages
"""

import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.integrations.whatsapp_client import get_whatsapp_client
from app.models.event import Event
from app.models.compliance_signal import ComplianceSignal
from app.core.enums import EventType, ActorType


class NotificationService:
    """
    Service for sending outbound WhatsApp messages with compliance tracking.
    """

    def __init__(self):
        self.client = get_whatsapp_client()

    async def send_message(
        self,
        to_phone: str,
        message: str,
        tenant_id: str,
        whatsapp_account_id: str,
        message_type: str = "notification",
        related_inquiry_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message and record the event.

        Args:
            to_phone: Recipient phone number
            message: Message content
            tenant_id: Tenant ID
            whatsapp_account_id: WhatsApp account ID used for sending
            message_type: Type of message (notification, response, command_result, etc.)
            related_inquiry_id: Related inquiry ID if applicable
            db: Database session for event logging

        Returns:
            Dict with send result and message ID
        """
        try:
            # Send the message
            result = await self.client.send_message(to_phone, message)

            # Record successful send event
            if db:
                event = Event(
                    id=str(uuid.uuid4()),
                    event_type=EventType.MESSAGE_SENT,
                    actor=ActorType.SYSTEM,
                    tenant_id=tenant_id,
                    whatsapp_account_id=whatsapp_account_id,
                    inquiry_id=related_inquiry_id,
                    payload={
                        "message_id": result.get("messages", [{}])[0].get("id"),
                        "to": to_phone,
                        "message_type": message_type,
                        "content": message,
                        "whatsapp_result": result
                    }
                )
                db.add(event)
                db.commit()

            return {
                "status": "sent",
                "message_id": result.get("messages", [{}])[0].get("id"),
                "whatsapp_result": result
            }

        except Exception as e:
            # Record failed send event and compliance signal
            if db:
                # Event for failed send
                event = Event(
                    id=str(uuid.uuid4()),
                    event_type=EventType.FAILED_SEND,
                    actor=ActorType.SYSTEM,
                    tenant_id=tenant_id,
                    whatsapp_account_id=whatsapp_account_id,
                    inquiry_id=related_inquiry_id,
                    payload={
                        "to": to_phone,
                        "message_type": message_type,
                        "content": message,
                        "error": str(e)
                    }
                )
                db.add(event)

                # Compliance signal for failed send
                signal = ComplianceSignal(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    whatsapp_account_id=whatsapp_account_id,
                    event_type=EventType.FAILED_SEND,
                    payload={
                        "recipient": to_phone,
                        "message_type": message_type,
                        "error": str(e)
                    }
                )
                db.add(signal)
                db.commit()

            return {
                "status": "failed",
                "error": str(e)
            }

    async def send_customer_response(
        self,
        customer_phone: str,
        response_message: str,
        tenant_id: str,
        whatsapp_account_id: str,
        inquiry_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Send a response to a customer inquiry.

        Args:
            customer_phone: Customer's phone number
            response_message: The response message
            tenant_id: Tenant ID
            whatsapp_account_id: WhatsApp account ID
            inquiry_id: Related inquiry ID
            db: Database session

        Returns:
            Send result
        """
        return await self.send_message(
            to_phone=customer_phone,
            message=response_message,
            tenant_id=tenant_id,
            whatsapp_account_id=whatsapp_account_id,
            message_type="customer_response",
            related_inquiry_id=inquiry_id,
            db=db
        )

    async def send_command_result(
        self,
        seller_phone: str,
        result_message: str,
        tenant_id: str,
        whatsapp_account_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Send command execution result to seller.

        Args:
            seller_phone: Seller's phone number
            result_message: Formatted command result
            tenant_id: Tenant ID
            whatsapp_account_id: WhatsApp account ID
            db: Database session

        Returns:
            Send result
        """
        return await self.send_message(
            to_phone=seller_phone,
            message=result_message,
            tenant_id=tenant_id,
            whatsapp_account_id=whatsapp_account_id,
            message_type="command_result",
            db=db
        )

    async def send_system_notification(
        self,
        recipient_phone: str,
        notification_message: str,
        tenant_id: str,
        whatsapp_account_id: str,
        notification_type: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Send a system notification.

        Args:
            recipient_phone: Recipient phone number
            notification_message: Notification content
            tenant_id: Tenant ID
            whatsapp_account_id: WhatsApp account ID
            notification_type: Type of notification
            db: Database session

        Returns:
            Send result
        """
        return await self.send_message(
            to_phone=recipient_phone,
            message=notification_message,
            tenant_id=tenant_id,
            whatsapp_account_id=whatsapp_account_id,
            message_type=f"system_{notification_type}",
            db=db
        )


# Global service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create the global notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
