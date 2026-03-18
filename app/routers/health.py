# Liveness/Readiness endpoint

"""
Health check endpoint
- Used by load balancers, CI, and uptime monitors
- Confirms app boot + database connectivity
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check(db: Session = Depends(get_db)):
    # Simple DB ping (safe, fast, transactional)
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "ok",
    }