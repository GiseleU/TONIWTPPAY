"""
Parse seller/customer WhatsApp messages.

This service analyzes incoming WhatsApp messages to determine if they are:
1. Seller commands (CONFIRM, DROP, SUMMARY)
2. Customer inquiries
3. Product entries (Phase 4)

Commands are executed immediately, while inquiries are stored for seller processing.
"""

import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.seller_command_service import parse_seller_command, execute_seller_command, CommandError
from app.models.product import Product


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


# ========================
# Phase 4: Product Entry Parsing
# ========================

def parse_product_entry(message_text: str, tenant_id: str, db: Session) -> Dict[str, Any]:
    """
    Parse product entry in format: "Product Name Quantity Price"
    
    Handles both modes:
    - Chat Entry: "Juice 2 800" (manual entry)
    - Click Selection: Product selected from catalog
    
    Args:
        message_text: The product entry text (e.g., "Juice 2 800")
        tenant_id: Tenant ID for catalog lookup
        db: Database session
        
    Returns:
        Dict with:
        - 'mode': 'chat_entry' or 'click_selection'
        - 'product_name': str
        - 'quantity': int
        - 'unit_price': int
        - 'total_price': int
        - 'is_done': bool (True if "DONE" signal)
        - 'catalog_products': List[Product] (if catalog exists)
    """
    message_text = message_text.strip().upper()
    
    # Handle DONE signal
    if message_text == "DONE":
        return {
            'mode': 'chat_entry',
            'is_done': True,
            'product_name': None,
            'quantity': None,
            'unit_price': None,
            'total_price': None,
            'catalog_products': _get_catalog_products(tenant_id, db)
        }
    
    # Check if catalog exists for this tenant
    catalog_products = _get_catalog_products(tenant_id, db)
    has_catalog = len(catalog_products) > 0
    
    # Parse product entry pattern: "Product Name Quantity Price"
    # Example: "Juice 2 800" -> product_name="Juice", quantity=2, unit_price=800
    product_match = re.match(r"^(.+?)\s+(\d+)\s+(\d+)$", message_text)
    
    if product_match:
        product_name = product_match.group(1).strip()
        quantity = int(product_match.group(2))
        unit_price = int(product_match.group(3))
        total_price = quantity * unit_price
        
        # Determine mode based on catalog existence
        # If catalog exists and product matches a catalog item, it's click selection
        mode = 'click_selection' if has_catalog and _is_catalog_product(product_name, catalog_products) else 'chat_entry'
        
        return {
            'mode': mode,
            'is_done': False,
            'product_name': product_name,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': total_price,
            'catalog_products': catalog_products
        }
    
    # Not a valid product entry
    raise ValueError(f"Invalid product entry format: {message_text}. Use: Product Name Quantity Price (e.g., Juice 2 800)")


def _get_catalog_products(tenant_id: str, db) -> List[Product]:
    """
    Get active products from catalog for a tenant.
    
    Args:
        tenant_id: Tenant ID
        db: Database session (can be None for chat-only mode)
        
    Returns:
        List of active Product objects
    """
    if db is None:
        return []  # No catalog available in chat-only mode
    
    return db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.is_active == True
    ).all()


def _is_catalog_product(product_name: str, catalog_products: List[Product]) -> bool:
    """
    Check if a product name matches any product in the catalog.
    
    Args:
        product_name: Product name to check
        catalog_products: List of catalog products
        
    Returns:
        True if product exists in catalog
    """
    product_name_upper = product_name.upper()
    return any(p.name.upper() == product_name_upper for p in catalog_products)


def detect_entry_mode(tenant_id: str, db: Session) -> str:
    """
    Detect which product entry mode to use based on catalog existence.
    
    Args:
        tenant_id: Tenant ID
        db: Database session
        
    Returns:
        'click_selection' if catalog exists, 'chat_entry' otherwise
    """
    catalog_products = _get_catalog_products(tenant_id, db)
    return 'click_selection' if len(catalog_products) > 0 else 'chat_entry'


def format_product_selection_message(tenant_id: str, db: Session) -> str:
    """
    Format a product selection message based on catalog.
    
    Args:
        tenant_id: Tenant ID
        db: Database session
        
    Returns:
        Formatted message for product selection
    """
    catalog_products = _get_catalog_products(tenant_id, db)
    
    if len(catalog_products) == 0:
        # No catalog - use chat entry mode
        return "Andika ibicuruzwa: Izina Ry'ikiguzo、数量 Price\n例: Juice 2 800"
    
    # Build product list for click selection
    lines = ["Hitamo igicuruzwa:"]
    for i, product in enumerate(catalog_products, 1):
        lines.append(f"{i}. {product.name} - {int(product.price)} RWF")
    lines.append("")
    lines.append("CG andika: Izina Quantity Price")
    
    return "\n".join(lines)
