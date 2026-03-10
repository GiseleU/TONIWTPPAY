"""
Application configuration

Phase 0:
- Load environment variables
- Fail fast if required settings are missing
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.DATABASE_URL: str | None = os.getenv("DATABASE_URL")
        self.VERIFY_TOKEN: str | None = os.getenv("VERIFY_TOKEN")

        if not self.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")

        if not self.VERIFY_TOKEN:
            raise RuntimeError("VERIFY_TOKEN is not set")


settings = Settings()