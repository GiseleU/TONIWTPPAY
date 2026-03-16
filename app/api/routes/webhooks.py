from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.webhook_service import handle_whatsapp_message, handle_momo_webhook
from app.schemas.webhook import MomoWebhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ------------------------------
# POST handler for WhatsApp messages (Twilio)
# ------------------------------
@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle incoming WhatsApp messages from Twilio.
    Expects form-encoded data: MessageSid, From, To, Body
    """
    form = await request.form()

    message_id = form.get("MessageSid")
    from_number = form.get("From", "").replace("whatsapp:", "")
    to_number = form.get("To", "").replace("whatsapp:", "")
    text = form.get("Body", "")

    if not message_id or not from_number:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid Twilio payload. MessageSid={message_id}, From={from_number}",
        )

    standardized_payload = {
        "message_id": message_id,
        "phone_number_id": to_number,
        "from": from_number,
        "to": to_number,
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