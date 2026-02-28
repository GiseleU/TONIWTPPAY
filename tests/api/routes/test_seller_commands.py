import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.services.seller_command_service import CommandError


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {
        "tenant-id": "tenant-123",
        "seller-id": "seller-001",
    }


# -----------------------------
# Happy Path Tests
# -----------------------------
def test_execute_confirm_command_success(client, auth_headers, monkeypatch):
    def mock_execute(command, seller_id, tenant_id, db):
        return {
            "status": "ok",
            "inquiry_id": "T1001",
            "new_status": "confirmed",
        }

    monkeypatch.setattr(
        "app.api.routes.seller_commands.execute_seller_command",
        mock_execute,
    )

    response = client.post(
        "/seller-commands/execute",
        json={"command": "CONFIRM T1001 500"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["new_status"] == "confirmed"


def test_execute_drop_command_success(client, auth_headers, monkeypatch):
    def mock_execute(command, seller_id, tenant_id, db):
        return {
            "status": "ok",
            "inquiry_id": "T1001",
            "new_status": "dropped",
        }

    monkeypatch.setattr(
        "app.api.routes.seller_commands.execute_seller_command",
        mock_execute,
    )

    response = client.post(
        "/seller-commands/execute",
        json={"command": "DROP T1001"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["new_status"] == "dropped"


def test_execute_summary_command_success(client, auth_headers, monkeypatch):
    def mock_execute(command, seller_id, tenant_id, db):
        return {
            "status": "ok",
            "summary": [
                {"id": "T1001", "status": "new", "amount": None},
            ],
        }

    monkeypatch.setattr(
        "app.api.routes.seller_commands.execute_seller_command",
        mock_execute,
    )

    response = client.post(
        "/seller-commands/execute",
        json={"command": "SUMMARY"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "summary" in response.json()


# -----------------------------
# Validation & Auth Errors
# -----------------------------
def test_missing_command_returns_422(client, auth_headers):
    response = client.post(
        "/seller-commands/execute",
        json={},
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert "command" in str(response.json())


def test_invalid_json_returns_422(client, auth_headers):
    response = client.post(
        "/seller-commands/execute",
        data="not-json",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_missing_auth_headers_returns_403(client):
    response = client.post(
        "/seller-commands/execute",
        json={"command": "SUMMARY"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Seller authentication required"


# -----------------------------
# Error Mapping from Service
# -----------------------------
def test_command_error_maps_to_400(client, auth_headers, monkeypatch):
    def mock_execute(command, seller_id, tenant_id, db):
        raise CommandError("Illegal transition")

    monkeypatch.setattr(
        "app.api.routes.seller_commands.execute_seller_command",
        mock_execute,
    )

    response = client.post(
        "/seller-commands/execute",
        json={"command": "CONFIRM T1001 500"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Illegal transition"


def test_unexpected_error_maps_to_500(client, auth_headers, monkeypatch):
    def mock_execute(command, seller_id, tenant_id, db):
        raise RuntimeError("DB is down")

    monkeypatch.setattr(
        "app.api.routes.seller_commands.execute_seller_command",
        mock_execute,
    )

    response = client.post(
        "/seller-commands/execute",
        json={"command": "SUMMARY"},
        headers=auth_headers,
    )

    assert response.status_code == 500
    assert "Unexpected server error" in response.json()["detail"]