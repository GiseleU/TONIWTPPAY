# # tests/routers/test_whatsapp_router.py
# import pytest
# from fastapi.testclient import TestClient
# from unittest.mock import AsyncMock, patch, ANY
# from app.main import app
# from fastapi import HTTPException
# from app.core.config import settings


# # ----------------------------
# # GET webhook verification
# # ----------------------------
# def test_verify_webhook_success(client: TestClient):
#     original_token = settings.VERIFY_TOKEN
#     settings.VERIFY_TOKEN = "test-token"

#     try:
#         response = client.get(
#             "/webhooks/whatsapp",
#             params={
#                 "hub.mode": "subscribe",
#                 "hub.challenge": "12345",
#                 "hub.verify_token": "test-token"
#             }
#         )
#         assert response.status_code == 200
#         assert response.json() == 12345
#     finally:
#         settings.VERIFY_TOKEN = original_token


# def test_verify_webhook_failure(client: TestClient):
#     original_token = settings.VERIFY_TOKEN
#     settings.VERIFY_TOKEN = "test-token"

#     try:
#         response = client.get(
#             "/webhooks/whatsapp",
#             params={
#                 "hub.mode": "subscribe",
#                 "hub.challenge": "12345",
#                 "hub.verify_token": "wrong-token"
#             }
#         )
#         assert response.status_code == 403
#         assert response.json()["detail"] == "Verification token mismatch"
#     finally:
#         settings.VERIFY_TOKEN = original_token


# # ----------------------------
# # POST webhook delegation (pure router test)
# # ----------------------------
# @pytest.mark.asyncio
# async def test_whatsapp_webhook_delegates_to_service(client: TestClient):
#     payload = {"entry": [{"changes": [{"value": {"messages": [{"from": "250700000001", "text": "Hello"}]}}]}]}

#     with patch("app.routers.whatsapp.parse_whatsapp_payload", return_value={"from": "250700000001", "text": "Hello"}), \
#          patch("app.routers.whatsapp.handle_message", new_callable=AsyncMock) as mock_handle_message:

#         response = client.post("/webhooks/whatsapp", json=payload)

#         # Router delegates to service
#         mock_handle_message.assert_awaited_once_with(
#             db=ANY,
#             seller_phone="250700000001",
#             message="Hello"
#         )
#         assert response.status_code == 200
#         assert response.json() == {"status": "success"}


# @pytest.mark.asyncio
# async def test_whatsapp_webhook_invalid_payload_returns_422(client: TestClient):
#     payload = {"wrong": "data"}

#     response = client.post("/webhooks/whatsapp", json=payload)
#     assert response.status_code == 422
#     assert "Invalid payload structure" in response.json()["detail"]


# @pytest.mark.asyncio
# async def test_whatsapp_webhook_service_raises_404(client: TestClient):
#     payload = {"entry": [{"changes": [{"value": {"messages": [{"from": "250700000002", "text": "Hi"}]}}]}]}

#     async def raise_404(*args, **kwargs):
#         raise HTTPException(status_code=404, detail="Seller not onboarded or inactive")

#     with patch("app.routers.whatsapp.parse_whatsapp_payload", return_value={"from": "250700000002", "text": "Hi"}), \
#          patch("app.routers.whatsapp.handle_message", new_callable=AsyncMock) as mock_handle_message:

#         mock_handle_message.side_effect = raise_404

#         response = client.post("/webhooks/whatsapp", json=payload)
#         assert response.status_code == 404
#         assert response.json()["detail"] == "Seller not onboarded or inactive"


# @pytest.mark.asyncio
# async def test_whatsapp_webhook_service_raises_unexpected_error(client: TestClient):
#     payload = {"entry": [{"changes": [{"value": {"messages": [{"from": "250700000003", "text": "Hi"}]}}]}]}

#     async def raise_error(*args, **kwargs):
#         raise ValueError("Unexpected")

#     with patch("app.routers.whatsapp.parse_whatsapp_payload", return_value={"from": "250700000003", "text": "Hi"}), \
#          patch("app.routers.whatsapp.handle_message", new_callable=AsyncMock) as mock_handle_message:

#         mock_handle_message.side_effect = raise_error

#         response = client.post("/webhooks/whatsapp", json=payload)
#         assert response.status_code == 500
#         assert response.json()["detail"] == "Processing error"


# tests/routers/test_whatsapp_router.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, ANY
from fastapi import HTTPException

from app.main import app
from app.core.config import settings


# ----------------------------
# Test client fixture
# ----------------------------
@pytest.fixture
def client():
    return TestClient(app)


# ----------------------------
# GET webhook verification
# ----------------------------
def test_verify_webhook_success(client: TestClient):
    original_token = settings.VERIFY_TOKEN
    settings.VERIFY_TOKEN = "test-token"

    try:
        response = client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "12345",
                "hub.verify_token": "test-token"
            }
        )
        assert response.status_code == 200
        assert response.json() == 12345
    finally:
        settings.VERIFY_TOKEN = original_token


def test_verify_webhook_failure(client: TestClient):
    original_token = settings.VERIFY_TOKEN
    settings.VERIFY_TOKEN = "test-token"

    try:
        response = client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "12345",
                "hub.verify_token": "wrong-token"
            }
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Verification token mismatch"
    finally:
        settings.VERIFY_TOKEN = original_token


# ----------------------------
# POST webhook delegation
# ----------------------------
@pytest.mark.asyncio
async def test_whatsapp_webhook_delegates_to_service(client: TestClient):
    payload = {"dummy": "data"}

    parsed = {
        "from": "250700000001",
        "text": "Hello"
    }

    with patch("app.routers.whatsapp.parse_whatsapp_payload", return_value=parsed), \
         patch("app.routers.whatsapp.handle_message", new_callable=AsyncMock) as mock_handle_message:

        response = client.post("/webhooks/whatsapp", json=payload)

        mock_handle_message.assert_awaited_once_with(
            db=ANY,
            seller_phone="250700000001",
            message="Hello"
        )

        assert response.status_code == 200
        assert response.json() == {"status": "success"}


# ----------------------------
# Missing field → 422
# ----------------------------
@pytest.mark.asyncio
async def test_whatsapp_webhook_missing_phone_number_id_returns_422(client: TestClient):
    payload = {"dummy": "data"}

    parsed = {
        "from": "250700000001",
        "text": "Hello"
    }

    def raise_keyerror(*args, **kwargs):
        raise KeyError("phone_number_id")

    with patch("app.routers.whatsapp.parse_whatsapp_payload", side_effect=raise_keyerror):
        response = client.post("/webhooks/whatsapp", json=payload)

        assert response.status_code == 422
        assert "Invalid payload structure" in response.json()["detail"]


# ----------------------------
# Service raises 404 → propagate
# ----------------------------
@pytest.mark.asyncio
async def test_whatsapp_webhook_service_raises_404(client: TestClient):
    payload = {"dummy": "data"}

    parsed = {
        "from": "250700000002",
        "text": "Hi"
    }

    with patch("app.routers.whatsapp.parse_whatsapp_payload", return_value=parsed), \
         patch("app.routers.whatsapp.handle_message", new_callable=AsyncMock) as mock_handle_message:

        mock_handle_message.side_effect = HTTPException(
            status_code=404,
            detail="Seller not onboarded or inactive"
        )

        response = client.post("/webhooks/whatsapp", json=payload)

        assert response.status_code == 404
        assert response.json()["detail"] == "Seller not onboarded or inactive"


# ----------------------------
# Unexpected error → 500
# ----------------------------
@pytest.mark.asyncio
async def test_whatsapp_webhook_service_raises_unexpected_error(client: TestClient):
    payload = {"dummy": "data"}

    parsed = {
        "from": "250700000003",
        "text": "Hi"
    }

    with patch("app.routers.whatsapp.parse_whatsapp_payload", return_value=parsed), \
         patch("app.routers.whatsapp.handle_message", new_callable=AsyncMock) as mock_handle_message:

        mock_handle_message.side_effect = Exception("Unexpected")

        response = client.post("/webhooks/whatsapp", json=payload)

        assert response.status_code == 500
        assert response.json()["detail"] == "Processing error"
