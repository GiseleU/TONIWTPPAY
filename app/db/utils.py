# app/db/utils.py
import uuid

def generate_uuid() -> str:
    """
    Generate a UUID string for primary key default.
    """
    return str(uuid.uuid4())