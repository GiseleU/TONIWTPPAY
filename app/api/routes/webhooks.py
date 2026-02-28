from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.webhook_service import handle_whatsapp_message, handle_momo_webhook
from app.schemas.webhook import WhatsappMessage, MomoWebhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

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
