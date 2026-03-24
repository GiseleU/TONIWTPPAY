# app/services/eod_scheduler.py

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.enums import CoexistenceStatus
from app.db.models_import import ConversationState, Tenant
from app.db.session import SessionLocal
from app.integrations.whatsapp_client import get_whatsapp_client
from app.services.summary_service import get_today_summary
from app.services.whatsapp_service import build_summary

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def send_eod_reports() -> None:
    """
    Sends end-of-day summary to every active tenant whose seller has sent a message
    in the past 24 hours (Meta's customer-initiated conversation window).
    Runs at 20:00 Kigali time (18:00 UTC).
    """
    db = SessionLocal()
    client = get_whatsapp_client()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    try:
        tenants = (
            db.query(Tenant)
            .filter(Tenant.coexistence_status == CoexistenceStatus.ACTIVE)
            .all()
        )

        for tenant in tenants:
            if not tenant.phone_number:
                continue

            state = (
                db.query(ConversationState)
                .filter(
                    ConversationState.tenant_id == tenant.id,
                    ConversationState.seller_phone == tenant.phone_number,
                )
                .first()
            )

            if not state or not state.last_message_at:
                continue

            # Ensure last_message_at is timezone-aware for comparison
            last_msg = state.last_message_at
            if last_msg.tzinfo is None:
                last_msg = last_msg.replace(tzinfo=timezone.utc)

            if last_msg < cutoff:
                continue  # Outside Meta's 24h window — cannot send

            try:
                # "today" in Kigali time is still today at 20:00 local (18:00 UTC)
                kigali_now = datetime.now(timezone.utc) + timedelta(hours=2)
                today = get_today_summary(db, tenant.id, kigali_now.date())
                message = build_summary(today)
                await client.send_message(tenant.phone_number, f"📅 End of day report\n\n{message}")
                logger.info(f"EOD report sent to tenant={tenant.id} phone={tenant.phone_number}")
            except Exception as e:
                logger.error(f"Failed to send EOD report to tenant={tenant.id}: {e}")

    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(
        send_eod_reports,
        trigger=CronTrigger(hour=18, minute=0, timezone="UTC"),  # 20:00 Kigali (UTC+2)
        id="eod_report",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("EOD scheduler started — reports will fire daily at 20:00 Kigali time")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("EOD scheduler stopped")
