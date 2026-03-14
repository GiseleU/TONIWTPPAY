#!/usr/bin/env python3
"""
Setup script to create your tenant and WhatsApp account.
Run this locally or on Render to set up your data.
"""

import uuid
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.whatsapp_account import WhatsAppAccount
from app.core.enums import CoexistenceStatus


def setup_tenant(
    tenant_name: str,
    whatsapp_number: str,  # Meta-generated test number
    seller_phone_number: str  # Your personal WhatsApp number
):
    """Create tenant and WhatsApp account"""
    
    db = next(get_db())
    
    try:
        # 1️⃣ Check existing WhatsApp account AND fix phone_number_id
        existing_wa = db.query(WhatsAppAccount).filter(
            WhatsAppAccount.phone_number == whatsapp_number
        ).first()
        
        if existing_wa:
            if existing_wa.phone_number_id != whatsapp_number:
                existing_wa.phone_number_id = whatsapp_number
                db.commit()
                print(f"🔧 FIXED: Updated phone_number_id to '{whatsapp_number}'")
            
            tenant = db.query(Tenant).filter(Tenant.id == existing_wa.tenant_id).first()
            print(f"✅ WhatsApp account ready: {whatsapp_number}")
            print(f"   Tenant: {tenant.name if tenant else 'Unknown'}")
            print(f"   phone_number_id: {existing_wa.phone_number_id}")
            return
        
        # 2️⃣ Check existing tenant by name (avoid duplicates)
        existing_tenant = db.query(Tenant).filter(Tenant.name == tenant_name).first()
        if existing_tenant:
            tenant = existing_tenant
            print(f"✅ Using existing tenant: {tenant_name}")
        else:
            # Create new tenant
            tenant = Tenant(
                id=str(uuid.uuid4()),
                name=tenant_name,
                phone_number=seller_phone_number,
                coexistence_status=CoexistenceStatus.ACTIVE
            )
            db.add(tenant)
            db.flush()
            print(f"✅ Created tenant: {tenant_name}")
        
        # 3️⃣ Create WhatsApp account with CRITICAL phone_number_id
        wa = WhatsAppAccount(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            phone_number=whatsapp_number,
            phone_number_id=whatsapp_number  # ← WEBHOOK LOOKUP KEY (was missing!)
        )
        db.add(wa)
        print(f"✅ Created WhatsApp account: {whatsapp_number}")
        print(f"   phone_number_id: {whatsapp_number} (webhook ready)")
        
        db.commit()
        print("\n🎉 Setup complete!")
        print(f"   Tenant: {tenant_name}")
        print(f"   WhatsApp number (Meta test): {whatsapp_number}")
        print(f"   Seller phone (your personal): {seller_phone_number}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python setup_tenant.py <tenant_name> <whatsapp_number> <seller_phone>")
        print("\nExample:")
        print("  python setup_tenant.py 'Test Businesss' '+15551936124' '+19096755835'")
        print("\nArguments:")
        print("  tenant_name: Your business name")
        print("  whatsapp_number: Meta phone_number_id (e.g. +15551936124)")
        print("  seller_phone: Your personal WhatsApp (receives notifications)")
        print("\n💡 phone_number_id must match webhook payload exactly!")
        sys.exit(1)
    
    tenant_name = sys.argv[1]
    whatsapp_number = sys.argv[2]
    seller_phone = sys.argv[3]
    
    setup_tenant(tenant_name, whatsapp_number, seller_phone)
