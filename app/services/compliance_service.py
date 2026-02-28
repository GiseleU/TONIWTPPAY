# Compliance monitoring and aggregation

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models import ComplianceSignal, Event
from app.core.enums import EventType
from app.core.datetime_utils import get_start_of_day, get_end_of_day
from datetime import date, timedelta
from typing import Dict


def aggregate_compliance_metrics(db: Session, tenant_id: str, start_date: date, end_date: date) -> Dict[str, int]:
    """
    Aggregate compliance metrics for a tenant over a date range.

    Returns counts of various compliance signals.
    """
    from app.models import Tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")

    start_dt = get_start_of_day(start_date)
    end_dt = get_end_of_day(end_date)

    # From ComplianceSignal table
    signals_query = db.query(ComplianceSignal).filter(
        and_(
            ComplianceSignal.tenant_id == tenant_id,
            ComplianceSignal.created_at >= start_dt,
            ComplianceSignal.created_at <= end_dt
        )
    )

    # From Events (for backward compatibility or additional)
    events_query = db.query(Event).filter(
        and_(
            Event.tenant_id == tenant_id,
            Event.created_at >= start_dt,
            Event.created_at <= end_dt,
            Event.event_type.in_([
                EventType.OPT_OUT,
                EventType.BLOCKED_SEND,
                EventType.FAILED_SEND,
                EventType.QUALITY_WARNING
            ])
        )
    )

    metrics = {
        "opt_outs": signals_query.filter(ComplianceSignal.event_type == "opt_out").count() +
                   events_query.filter(Event.event_type == EventType.OPT_OUT).count(),
        "blocked_sends": signals_query.filter(ComplianceSignal.event_type == "blocked_send").count() +
                        events_query.filter(Event.event_type == EventType.BLOCKED_SEND).count(),
        "failed_sends": signals_query.filter(ComplianceSignal.event_type == "failed_send").count() +
                       events_query.filter(Event.event_type == EventType.FAILED_SEND).count(),
        "quality_warnings": signals_query.filter(ComplianceSignal.event_type == "quality_warning").count() +
                           events_query.filter(Event.event_type == EventType.QUALITY_WARNING).count(),
    }

    return metrics
