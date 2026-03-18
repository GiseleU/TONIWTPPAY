# app/services/daily_summary_job.py
import asyncio
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.tenant import Tenant
from app.services.summary_service import generate_daily_summary
from app.core.datetime_utils import get_yesterday
from app.core.logging import logger
from app.core.enums import CoexistenceStatus


async def run_daily_summary_job():
    """
    Background job to generate daily summaries for all active tenants.
    Processes yesterday's transaction data for each active tenant.
    """
    db: Session = next(get_db())
    try:
        summary_date = get_yesterday()
        tenants = db.query(Tenant).filter(
            Tenant.coexistence_status == CoexistenceStatus.ACTIVE
        ).all()

        for tenant in tenants:
            try:
                generate_daily_summary(db, tenant.id, summary_date)
                logger.info(f"Daily summary generated for tenant {tenant.id} ({summary_date})")
            except Exception as e:
                # Log the error, continue with other tenants
                logger.error(f"Error generating summary for tenant {tenant.id}: {e}", exc_info=True)

        db.commit()
    finally:
        db.close()


def trigger_daily_summary_job():
    """
    Trigger the daily summary job synchronously via asyncio.
    """
    asyncio.run(run_daily_summary_job())