# Daily funnel + revenue aggregation

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from app.models import Tenant, Order, Payment, Inquiry, Event, DailySummary
from app.core.enums import EventType
from app.core.datetime_utils import get_start_of_day, get_end_of_day
from datetime import date, datetime, timezone
from decimal import Decimal


def generate_daily_summary(db: Session, tenant_id: str, summary_date: date) -> DailySummary:
    """
    Generate and store daily summary for a tenant on a specific date.

    Aggregates revenue, orders, inquiries, and compliance metrics.
    Ensures idempotency by updating existing summary if present.
    """
    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")

    # Check if summary already exists
    existing = db.query(DailySummary).options(joinedload(DailySummary.tenant)).filter(
        and_(DailySummary.tenant_id == tenant_id, DailySummary.summary_date == summary_date)
    ).first()

    if existing:
        summary = existing
    else:
        summary = DailySummary(
            id=f"DS{summary_date.strftime('%Y%m%d')}{tenant_id[:4].upper()}",
            tenant_id=tenant_id,
            summary_date=summary_date,
        )
        summary.tenant = tenant
        db.add(summary)

    start_dt = get_start_of_day(summary_date)
    end_dt = get_end_of_day(summary_date)

    # Aggregate revenue & orders
    orders_query = db.query(Order).filter(
        and_(Order.tenant_id == tenant_id, Order.created_at >= start_dt, Order.created_at <= end_dt)
    )
    summary.total_orders = orders_query.count()
    summary.total_revenue = sum(order.amount for order in orders_query.all()) or Decimal(0)

    # Paid orders and revenue
    paid_orders = orders_query.filter(Order.status == "paid").all()
    summary.paid_orders = len(paid_orders)
    summary.paid_revenue = sum(order.amount for order in paid_orders) or Decimal(0)

    # Funnel metrics
    inquiries_query = db.query(Inquiry).filter(
        and_(Inquiry.tenant_id == tenant_id, Inquiry.created_at >= start_dt, Inquiry.created_at <= end_dt)
    )
    summary.total_inquiries = inquiries_query.count()
    summary.confirmed_inquiries = inquiries_query.filter(Inquiry.status == "confirmed").count()
    summary.dropped_inquiries = inquiries_query.filter(Inquiry.status == "dropped").count()

    # Compliance metrics from events
    events_query = db.query(Event).filter(
        and_(Event.tenant_id == tenant_id, Event.created_at >= start_dt, Event.created_at <= end_dt)
    )
    summary.opt_outs = events_query.filter(Event.event_type == EventType.OPT_OUT).count()
    summary.blocked_sends = events_query.filter(Event.event_type == EventType.BLOCKED_SEND).count()
    summary.failed_sends = events_query.filter(Event.event_type == EventType.FAILED_SEND).count()
    summary.quality_warnings = events_query.filter(Event.event_type == EventType.QUALITY_WARNING).count()

    db.commit()
    db.refresh(summary)
    return summary
