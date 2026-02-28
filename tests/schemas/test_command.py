import pytest
from pydantic import ValidationError
from app.schemas.command import SellerCommandRequest


def test_seller_command_request_valid():
    """Test valid SellerCommandRequest instantiation"""
    data = {"command": "CONFIRM T1001 500"}
    req = SellerCommandRequest(**data)
    assert req.command == "CONFIRM T1001 500"


def test_seller_command_request_missing_command():
    """Test SellerCommandRequest validation error for missing command"""
    with pytest.raises(ValidationError):
        SellerCommandRequest()  # Missing command field
