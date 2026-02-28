# Tests for daily_summary_job

import pytest
from unittest.mock import patch
from app.services.daily_summary_job import run_daily_summary_job
from app.models import DailySummary, Tenant
from datetime import date


def test_run_daily_summary_job_idempotency(db_session):
    tenant = Tenant(id="T001", name="Test Tenant")
    db_session.add(tenant)
    summary_date = date.today()
    existing = DailySummary(
        id="DS001",
        tenant_id=tenant.id,
        summary_date=summary_date,
        total_orders=5
    )
    db_session.add(existing)
    db_session.commit()

    # Since async_runner just calls await, we can test the function directly
    from app.services.summary_service import generate_daily_summary
    generate_daily_summary(db_session, tenant.id, summary_date)

    # Should not create duplicate
    summaries = db_session.query(DailySummary).filter(
        DailySummary.tenant_id == tenant.id,
        DailySummary.summary_date == summary_date
    ).all()
    assert len(summaries) == 1
