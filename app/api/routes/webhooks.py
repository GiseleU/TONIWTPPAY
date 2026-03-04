# from fastapi import APIRouter, HTTPException, Depends
# from sqlalchemy.orm import Session
# from app.db.session import get_db
# from app.services.webhook_service import handle_whatsapp_message, handle_momo_webhook
# from app.schemas.webhook import WhatsappMessage, MomoWebhook

# router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# @router.post("/whatsapp")
# async def whatsapp_webhook(request: WhatsappMessage, db: Session = Depends(get_db)):
#     payload = request.model_dump(by_alias=True)  # Convert to dict with 'from' key
#     try:
#         result = handle_whatsapp_message(payload, db)
#     except ValueError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except PermissionError as e:
#         raise HTTPException(status_code=403, detail=str(e))

#     return result


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



from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.webhook_service import handle_whatsapp_message, handle_momo_webhook
from app.schemas.webhook import WhatsappMessage, MomoWebhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# ----- Meta verification token -----
VERIFY_TOKEN = "gwizawtp_verify_2026"

# ------------------------------
# GET handler for WhatsApp webhook verification
# ------------------------------
@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
):
    if hub_verify_token != VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid verify token")
    return int(hub_challenge)


# ------------------------------
# POST handler for WhatsApp messages
# ------------------------------
@router.post("/whatsapp")
async def whatsapp_webhook(request: WhatsappMessage, db: Session = Depends(get_db)):
    payload = request.model_dump(by_alias=True)  # Convert to dict with 'from' key
    try:
        result = handle_whatsapp_message(payload, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return result


# ------------------------------
# POST handler for MoMo webhooks (unchanged)
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