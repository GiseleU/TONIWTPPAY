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

        if not self.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")


settings = Settings()