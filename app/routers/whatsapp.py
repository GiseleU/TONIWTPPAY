# app/routers/whatsapp.py
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.whatsapp_service import handle_message
from app.schemas.whatsapp import parse_whatsapp_payload
from app.core.config import settings

router = APIRouter()


# GET webhook verification
@router.get("/webhooks/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """Meta webhook verification endpoint."""
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification token mismatch")


# POST webhook
@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handles incoming messages from WhatsApp Cloud API.
    Delegates all business logic to `handle_message`.
    """
    try:
        payload = await request.json()
        msg_data = parse_whatsapp_payload(payload)
        seller_phone = msg_data["from"]
        message = msg_data["text"]

        # Delegate everything to service (tenant validation, workflow, commands)
        await handle_message(db=db, seller_phone=seller_phone, message=message)

    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Invalid payload structure: {e}")
    except HTTPException:
        raise  # propagate 404 or 403 from service
    except Exception as e:
        print(f"Error processing WhatsApp message: {e}")
        raise HTTPException(status_code=500, detail="Processing error")

    return {"status": "success"}