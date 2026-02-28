# Tests for DailySummary model

import pytest
from app.models import DailySummary, Tenant
from datetime import date


def test_daily_summary_creation(db_session):
    tenant = Tenant(id="T001", name="Test Tenant")
    db_session.add(tenant)
    summary_date = date.today()

    summary = DailySummary(
        id="DS001",
        tenant_id=tenant.id,
        summary_date=summary_date,
        total_orders=10,
        total_revenue=100.0
    )
    db_session.add(summary)
    db_session.commit()

    assert summary.id == "DS001"
    assert summary.total_orders == 10
