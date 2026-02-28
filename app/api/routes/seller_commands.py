# app/api/routes/seller_commands.py
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.seller_command_service import execute_seller_command, CommandError
from typing import Optional
from app.schemas.command import SellerCommandRequest

router = APIRouter(prefix="/seller-commands", tags=["seller-commands"])


@router.post("/execute")
async def execute_command(
    request: SellerCommandRequest,
    db: Session = Depends(get_db),
    tenant_id: Optional[str] = Header(None),  # Can come from auth headers / JWT
    seller_id: Optional[str] = Header(None)   # Can come from auth headers / JWT
):
    """
    Endpoint to execute seller commands.

    Supported commands:
      - CONFIRM T#### amount
      - DROP T####
      - SUMMARY

    Notes:
      - tenant_id and seller_id are required for authorization.
      - SUMMARY returns all inquiries for the tenant.
      - CONFIRM/DROP applies deterministic state transitions and records audit events.
    """
    command_text = request.command

    # Ensure authorization info is provided
    if not tenant_id or not seller_id:
        raise HTTPException(status_code=403, detail="Seller authentication required")

    try:
        # Execute the command in the service layer
        result = execute_seller_command(command_text, seller_id, tenant_id, db)
    except CommandError as e:
        # Invalid command format or illegal state transition
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")

    return result
