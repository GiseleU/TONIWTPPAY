# # app/routers/whatsapp.py
# from fastapi import APIRouter, Request, Depends, HTTPException, Query
# from sqlalchemy.orm import Session
# from app.db.session import get_db
# from app.services.whatsapp_service import handle_message
# from app.schemas.whatsapp import parse_whatsapp_payload
# from app.core.config import settings

# router = APIRouter()


# # --------------------------
# # GET webhook verification
# # --------------------------
# @router.get("/webhooks/whatsapp")
# async def verify_webhook(
#     hub_mode: str = Query(..., alias="hub.mode"),
#     hub_challenge: str = Query(..., alias="hub.challenge"),
#     hub_verify_token: str = Query(..., alias="hub.verify_token")
# ):
#     """Meta webhook verification endpoint."""
#     if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
#         return int(hub_challenge)
#     raise HTTPException(status_code=403, detail="Verification token mismatch")


# # --------------------------
# # POST webhook
# # --------------------------
# @router.post("/webhooks/whatsapp")
# async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
#     """
#     Handles incoming messages from WhatsApp Cloud API.
#     """
#     try:
#         payload = await request.json()

#         msg_data = parse_whatsapp_payload(payload)

#         # Extract required fields
#         seller_phone = msg_data["from"]
#         message = msg_data["text"]
#         phone_number_id = msg_data["phone_number_id"]

#         # Debug (optional - remove in prod)
#         print("📩 Incoming message:")
#         print("   From:", seller_phone)
#         print("   Phone Number ID:", phone_number_id)
#         print("   Message:", message)

#         await handle_message(
#             db=db,
#             seller_phone=seller_phone,
#             message=message,
#             phone_number_id=phone_number_id
#         )

#     except KeyError as e:
#         raise HTTPException(status_code=422, detail=f"Invalid payload structure: {e}")

#     except HTTPException:
#         raise  # propagate known errors

#     except Exception as e:
#         print(f"❌ Error processing WhatsApp message: {e}")
#         raise HTTPException(status_code=500, detail="Processing error")

#     return {"status": "success"}



# app/routers/whatsapp.py
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.whatsapp_service import handle_message
from app.schemas.whatsapp import parse_whatsapp_payload
from app.core.config import settings

router = APIRouter()


# --------------------------
# GET webhook verification
# --------------------------
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


# --------------------------
# POST webhook
# --------------------------
@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handles incoming messages from WhatsApp Cloud API.
    """

    try:
        payload = await request.json()
        msg_data = parse_whatsapp_payload(payload)

        # Extract fields
        seller_phone = msg_data["from"]          # sender's WhatsApp number
        seller_name = msg_data.get("name", "")   # sender's profile name
        message = msg_data["text"]

        # Debug (optional)
        print("📩 Incoming message:")
        print("   From (wa_id):", seller_phone)
        print("   Name:", seller_name)
        print("   Message:", message)

        await handle_message(
            db=db,
            seller_phone=seller_phone,
            message=message
        )

    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Invalid payload structure: {e}")

    except HTTPException:
        raise  # propagate known errors

    except Exception as e:
        print(f"❌ Error processing WhatsApp message: {e}")
        raise HTTPException(status_code=500, detail="Processing error")

    return {"status": "success"}