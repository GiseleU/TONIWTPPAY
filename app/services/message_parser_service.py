"""
Parse seller/customer WhatsApp messages.

This service analyzes incoming WhatsApp messages to determine if they are:
1. Seller commands (CONFIRM, DROP, SUMMARY)
2. Customer inquiries

Commands are executed immediately, while inquiries are stored for seller processing.
"""

import re
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.seller_command_service import parse_seller_command, execute_seller_command, CommandError


def parse_message_type(message_text: str) -> Dict[str, Any]:
    """
    Parse a WhatsApp message to determine its type.

    Args:
        message_text: The text content of the WhatsApp message

    Returns:
        Dict with keys:
        - 'type': 'command' or 'inquiry'
        - 'command': parsed command dict (if type is 'command')
        - 'is_valid_command': bool (if type is 'command')
    """
    message_text = message_text.strip().upper()

    # Try to parse as command
    try:
        command = parse_seller_command(message_text)
        return {
            'type': 'command',
            'command': command,
            'is_valid_command': True
        }
    except CommandError:
        # Not a valid command, treat as inquiry
        return {
            'type': 'inquiry',
            'command': None,
            'is_valid_command': False
        }


def process_incoming_message(
    message_text: str,
    sender_phone: str,
    tenant_id: str,
    db: Session
) -> Dict[str, Any]:
    """
    Process an incoming WhatsApp message.

    If it's a seller command, execute it and return the result.
    If it's a customer inquiry, return info for inquiry creation.

    Args:
        message_text: The message text
        sender_phone: Phone number of the sender
        tenant_id: Tenant ID
        db: Database session

    Returns:
        Dict with processing result
    """
    parsed = parse_message_type(message_text)

    if parsed['type'] == 'command':
        # Execute the command
        try:
            result = execute_seller_command(
                message_text,
                sender_phone,  # Use phone as seller_id for now
                tenant_id,
                db
            )
            return {
                'type': 'command_executed',
                'result': result,
                'response_message': _format_command_response(result)
            }
        except CommandError as e:
            return {
                'type': 'command_error',
                'error': str(e),
                'response_message': f"Command error: {str(e)}"
            }
    else:
        # Customer inquiry
        return {
            'type': 'inquiry',
            'message': message_text,
            'sender_phone': sender_phone,
            'tenant_id': tenant_id
        }


def _format_command_response(result: Dict[str, Any]) -> str:
    """
    Format a command execution result into a WhatsApp response message.

    Args:
        result: Command execution result

    Returns:
        Formatted response message
    """
    if result.get('status') != 'ok':
        return "Command failed"

    if 'summary' in result:
        # SUMMARY command response
        summary = result['summary']
        return f"""Daily Summary:
Orders: {summary['total_orders']} total, {summary['paid_orders']} paid (${summary['paid_revenue']:.2f})
Revenue: ${summary['total_revenue']:.2f} total, ${summary['paid_revenue']:.2f} paid
Inquiries: {summary['total_inquiries']} total, {summary['confirmed_inquiries']} confirmed, {summary['dropped_inquiries']} dropped
Compliance: {summary['opt_outs']} opt-outs, {summary['blocked_sends']} blocked, {summary['failed_sends']} failed"""

    elif 'inquiry_id' in result:
        # CONFIRM or DROP command response
        action = "confirmed" if result.get('new_status') == 'confirmed' else "dropped"
        return f"Inquiry {result['inquiry_id']} has been {action}"

    else:
        return "Command executed successfully"
