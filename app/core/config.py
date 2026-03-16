"""
Application configuration - Twilio WhatsApp Migration

Phase 1 Complete:
- DATABASE_URL required
- TWILIO_* vars (required for production, optional for dev)
- WHATSAPP_PHONE_NUMBER_ID alias maintained for compatibility
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.DATABASE_URL: str | None = os.getenv("DATABASE_URL")
        self.WHATSAPP_PHONE_NUMBER_ID: str | None = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.TWILIO_ACCOUNT_SID: str | None = os.getenv("TWILIO_ACCOUNT_SID")
        self.TWILIO_AUTH_TOKEN: str | None = os.getenv("TWILIO_AUTH_TOKEN")
        self.TWILIO_WHATSAPP_NUMBER: str | None = os.getenv("TWILIO_WHATSAPP_NUMBER")

        # TWILIO vars required for production, optional for local dev/testing
        missing_twilio = [v for v in [self.TWILIO_ACCOUNT_SID, self.TWILIO_AUTH_TOKEN, self.TWILIO_WHATSAPP_NUMBER] if not v]
        if missing_twilio and os.getenv("ENV") != "dev":
            raise RuntimeError(f"Missing TWILIO vars for production: {missing_twilio}")


settings = Settings()