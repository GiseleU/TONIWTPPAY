"""
Application configuration - WhatsApp Payments MVP

Required environment variables:
- DATABASE_URL: PostgreSQL URL
- WHATSAPP_PHONE_NUMBER_ID: Meta-generated phone number ID
- WHATSAPP_ACCESS_TOKEN: Meta WhatsApp Cloud API access token
- VERIFY_TOKEN: token used to verify webhook
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        # Database
        self.DATABASE_URL: str | None = os.getenv("DATABASE_URL")

        # WhatsApp Cloud API
        self.WHATSAPP_PHONE_NUMBER_ID: str | None = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.WHATSAPP_ACCESS_TOKEN: str | None = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.VERIFY_TOKEN: str | None = os.getenv("VERIFY_TOKEN")

        # Basic validation
        missing = [v for v in [self.DATABASE_URL, self.WHATSAPP_PHONE_NUMBER_ID,
                               self.WHATSAPP_ACCESS_TOKEN, self.VERIFY_TOKEN] if not v]
        if missing:
            raise RuntimeError(f"Missing required config variables: {missing}")


settings = Settings()