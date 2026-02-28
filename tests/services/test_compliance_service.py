# Tests for compliance_service

import pytest
from sqlalchemy.orm import Session
from app.services.compliance_service import aggregate_compliance_metrics
from app.models import ComplianceSignal, Tenant
from datetime import date


def test_aggregate_compliance_metrics(db_session: Session):
    tenant = Tenant(id="T001", name="Test Tenant")
    db_session.add(tenant)
    start_date = date.today()
    end_date = date.today()

    signal = ComplianceSignal(
        id="CS001",
        tenant_id=tenant.id,
        event_type="opt_out",
        created_at=start_date
    )
    db_session.add(signal)
    db_session.commit()

    metrics = aggregate_compliance_metrics(db_session, tenant.id, start_date, end_date)

    assert metrics["opt_outs"] == 1
    assert metrics["blocked_sends"] == 0
