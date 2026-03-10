# from fastapi import APIRouter, HTTPException, Depends, Query, Request
# from sqlalchemy.orm import Session
# from app.db.session import get_db
# from app.core.config import settings
# from app.services.webhook_service import handle_whatsapp_message, handle_momo_webhook
# from app.schemas.webhook import (
#     WhatsappMessage,
#     MomoWebhook,
#     parse_whatsapp_payload,
#     MetaWhatsAppWebhook,
# )

# router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# # ------------------------------
# # GET handler for WhatsApp webhook verification
# # ------------------------------
# @router.get("/whatsapp")
# async def verify_whatsapp_webhook(
#     hub_mode: str = Query(..., alias="hub.mode"),
#     hub_challenge: str = Query(..., alias="hub.challenge"),
#     hub_verify_token: str = Query(..., alias="hub.verify_token"),
# ):
#     if hub_verify_token != settings.VERIFY_TOKEN:
#         raise HTTPException(status_code=403, detail="Invalid verify token")
#     return int(hub_challenge)


# # ------------------------------
# # POST handler for WhatsApp messages
# # ------------------------------
# @router.post("/whatsapp")
# async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
#     """
#     Handle incoming WhatsApp messages from Meta.
    
#     Supports two payload formats:
#     1. Flat format (for testing): {"message_id": "...", "to": "...", "from": "...", "text": "..."}
#     2. Meta format (from WhatsApp API): {"object": "whatsapp_business_account", "entry": [...]}
#     """
#     # Get raw payload
#     payload = await request.json()
    
#     # Parse payload to standardized format
#     parsed_payload = parse_whatsapp_payload(payload)
    
#     # Extract the fields needed for the service
#     message_id = parsed_payload.get("message_id")
#     to = parsed_payload.get("to")
#     from_ = parsed_payload.get("from")
#     text = parsed_payload.get("text")
    
#     # Validate required fields
#     if not message_id or not to or not from_:
#         raise HTTPException(
#             status_code=422, 
#             detail=f"Invalid payload: missing required fields. Got: message_id={message_id}, to={to}, from={from_}"
#         )
    
#     # Create standardized payload for the service
#     standardized_payload = {
#         "message_id": message_id,
#         "to": to,
#         "from": from_,
#         "text": text,
#     }
    
#     try:
#         result = handle_whatsapp_message(standardized_payload, db)
#     except ValueError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except PermissionError as e:
#         raise HTTPException(status_code=403, detail=str(e))

#     return result


# # ------------------------------
# # POST handler for MoMo webhooks (unchanged)
# # ------------------------------
# @router.post("/momo")
# async def momo_webhook(request: MomoWebhook, db: Session = Depends(get_db)):
#     payload = request.model_dump()
#     try:
#         result = handle_momo_webhook(payload, db)
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except PermissionError as e:
#         raise HTTPException(status_code=403, detail=str(e))

#     return result




from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.services.webhook_service import handle_whatsapp_message, handle_momo_webhook
from app.schemas.webhook import (
    WhatsappMessage,
    MomoWebhook,
    parse_whatsapp_payload,
    MetaWhatsAppWebhook,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ------------------------------
# GET handler for WhatsApp webhook verification
# ------------------------------
@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
):
    if hub_verify_token != settings.VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid verify token")

    return int(hub_challenge)


# ------------------------------
# POST handler for WhatsApp messages
# ------------------------------
@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle incoming WhatsApp messages from Meta.

    Supports two payload formats:
    1. Flat format (for testing)
    2. Official Meta webhook format
    """

    payload = await request.json()

    parsed_payload = parse_whatsapp_payload(payload)

    message_id = parsed_payload.get("message_id")
    phone_number_id = parsed_payload.get("phone_number_id")
    to = parsed_payload.get("to")
    from_ = parsed_payload.get("from")
    text = parsed_payload.get("text")

    if not message_id or not phone_number_id or not from_:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid payload. message_id={message_id}, phone_number_id={phone_number_id}, from={from_}",
        )

    standardized_payload = {
        "message_id": message_id,
        "phone_number_id": phone_number_id,
        "to": to,
        "from": from_,
        "text": text,
    }

    try:
        result = handle_whatsapp_message(standardized_payload, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return result


# ------------------------------
# POST handler for MoMo webhooks
# ------------------------------
@router.post("/momo")
async def momo_webhook(request: MomoWebhook, db: Session = Depends(get_db)):
    payload = request.model_dump()

    try:
        result = handle_momo_webhook(payload, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return result