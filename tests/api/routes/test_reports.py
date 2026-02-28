# Tests for reports API

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Tenant
from datetime import date


def test_get_daily_summary(client: TestClient, db_session):
    tenant = Tenant(id="T001", name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()

    response = client.get(f"/reports/daily-summary?tenant_id={tenant.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == tenant.id
    assert "total_orders" in data


def test_get_compliance_metrics(client: TestClient, db_session):
    tenant = Tenant(id="T002", name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()
    start_date = date.today().isoformat()
    end_date = date.today().isoformat()

    response = client.get(f"/reports/compliance-metrics?tenant_id={tenant.id}&start_date={start_date}&end_date={end_date}")

    assert response.status_code == 200
    data = response.json()
    assert "opt_outs" in data
