#!/usr/bin/env python3
"""
Test script for WhatsApp Business API coexistence logic.

This script sets up test tenants with different coexistence statuses
and tests that only ACTIVE tenants can process WhatsApp webhooks.
"""

import httpx
import uuid
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.whatsapp_account import WhatsAppAccount
from app.models.contact import Contact
from app.models.inquiry import Inquiry
from app.models.event import Event
from app.core.enums import CoexistenceStatus

# API base URL
BASE_URL = "http://localhost:8001"

def setup_test_data(db: Session):
    """Create test tenants with different coexistence statuses"""

    # Clean up existing test data - delete in correct order
    db.query(Event).filter(Event.tenant_id.like("test-%")).delete()
    db.query(Inquiry).filter(Inquiry.tenant_id.like("test-%")).delete()
    db.query(Contact).filter(Contact.tenant_id.like("test-%")).delete()
    db.query(WhatsAppAccount).filter(WhatsAppAccount.tenant_id.like("test-%")).delete()
    db.query(Tenant).filter(Tenant.id.like("test-%")).delete()
    db.commit()

    # Create tenants with different statuses
    tenants_data = [
        ("test-active", "Active Tenant", CoexistenceStatus.ACTIVE, "+250700000001"),
        ("test-pending", "Pending Tenant", CoexistenceStatus.PENDING, "+250700000002"),
        ("test-blocked", "Blocked Tenant", CoexistenceStatus.BLOCKED, "+250700000003"),
        ("test-suspended", "Suspended Tenant", CoexistenceStatus.SUSPENDED, "+250700000004"),
    ]

    tenants = []
    for tenant_id, name, status, phone in tenants_data:
        tenant = Tenant(
            id=tenant_id,
            name=name,
            coexistence_status=status
        )
        db.add(tenant)
        db.flush()  # Get ID

        # Create WhatsApp account
        wa = WhatsAppAccount(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            phone_number=phone
        )
        db.add(wa)
        tenants.append((tenant, wa))

    db.commit()
    return tenants

def test_webhook(tenant_name: str, phone_number: str, expected_status: int):
    """Test WhatsApp webhook for a specific tenant"""

    payload = {
        "message_id": f"test-{tenant_name}-{uuid.uuid4().hex[:8]}",
        "from": "+1234567890",
        "to": phone_number,
        "text": f"Test message for {tenant_name}"
    }

    print(f"\n🧪 Testing {tenant_name} (expected status: {expected_status})")
    print(f"   Payload: {payload}")

    try:
        with httpx.Client() as client:
            response = client.post(f"{BASE_URL}/webhooks/whatsapp", json=payload, timeout=5)
            print(f"   Response: {response.status_code} - {response.text}")

            if response.status_code == expected_status:
                print(f"   ✅ PASS: Got expected status {expected_status}")
                return True
            else:
                print(f"   ❌ FAIL: Expected {expected_status}, got {response.status_code}")
                return False

    except httpx.RequestError as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_momo_webhook(tenant_id: str, expected_status: int):
    """Test MoMo webhook for coexistence"""

    payload = {
        "transaction_id": f"txn-{tenant_id}-{uuid.uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "amount": 100.50,
        "status": "completed"
    }

    print(f"\n💰 Testing MoMo for {tenant_id} (expected status: {expected_status})")

    try:
        with httpx.Client() as client:
            response = client.post(f"{BASE_URL}/webhooks/momo", json=payload, timeout=5)
            print(f"   Response: {response.status_code} - {response.text}")

            if response.status_code == expected_status:
                print(f"   ✅ PASS: Got expected status {expected_status}")
                return True
            else:
                print(f"   ❌ FAIL: Expected {expected_status}, got {response.status_code}")
                return False

    except httpx.RequestError as e:
        print(f"   ❌ ERROR: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing WhatsApp Business API Coexistence Logic")
    print("=" * 60)

    # Get database session
    db = next(get_db())

    try:
        # Setup test data
        print("\n📝 Setting up test data...")
        tenants = setup_test_data(db)
        print(f"   Created {len(tenants)} test tenants")

        # Test WhatsApp webhooks
        print("\n📱 Testing WhatsApp Webhook Coexistence")
        print("-" * 40)

        results = []

        # ACTIVE tenant should succeed (200)
        tenant, wa = tenants[0]
        results.append(test_webhook("ACTIVE", wa.phone_number, 200))

        # Non-ACTIVE tenants should fail (403)
        for tenant, wa in tenants[1:]:
            results.append(test_webhook(tenant.coexistence_status.value.upper(), wa.phone_number, 403))

        # Test MoMo webhooks
        print("\n💳 Testing MoMo Webhook Coexistence")
        print("-" * 40)

        # ACTIVE tenant should succeed (200)
        tenant, _ = tenants[0]
        results.append(test_momo_webhook(tenant.id, 200))

        # Non-ACTIVE tenants should fail (403)
        for tenant, _ in tenants[1:]:
            results.append(test_momo_webhook(tenant.id, 403))

        # Summary
        print("\n📊 Test Results")
        print("-" * 40)
        passed = sum(results)
        total = len(results)
        print(f"Passed: {passed}/{total}")

        if passed == total:
            print("🎉 All coexistence tests PASSED!")
            return 0
        else:
            print("❌ Some tests FAILED!")
            return 1

    finally:
        db.close()

if __name__ == "__main__":
    exit(main())
