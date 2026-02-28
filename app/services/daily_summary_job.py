# Daily summary background job

import asyncio
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Tenant
from app.services.summary_service import generate_daily_summary
from app.core.datetime_utils import get_yesterday
from app.services.async_runner import run_background_job


async def run_daily_summary_job():
    """
    Background job to generate daily summaries for all active tenants.
    Runs daily, processing yesterday's data.
    """
    db: Session = next(get_db())
    try:
        summary_date = get_yesterday()
        tenants = db.query(Tenant).filter(Tenant.coexistence_status == "ACTIVE").all()

        for tenant in tenants:
            try:
                generate_daily_summary(db, tenant.id, summary_date)
            except Exception as e:
                # Log error, but continue with other tenants
                print(f"Error generating summary for tenant {tenant.id}: {e}")
                continue

        db.commit()
    finally:
        db.close()


# Function to trigger the job
def trigger_daily_summary_job():
    """Trigger the daily summary job asynchronously."""
    asyncio.run(run_background_job(run_daily_summary_job))
