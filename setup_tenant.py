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
        # Check if WhatsApp account already exists
        existing_wa = db.query(WhatsAppAccount).filter(
            WhatsAppAccount.phone_number == whatsapp_number
        ).first()
        
        if existing_wa:
            tenant = db.query(Tenant).filter(Tenant.id == existing_wa.tenant_id).first()
            print(f"✅ WhatsApp account already exists: {whatsapp_number}")
            print(f"   Tenant: {tenant.name if tenant else 'Unknown'}")
            return
        
        # Create new tenant
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=tenant_name,
            phone_number=seller_phone_number,  # Seller's personal WhatsApp
            coexistence_status=CoexistenceStatus.ACTIVE
        )
        db.add(tenant)
        db.flush()
        print(f"✅ Created tenant: {tenant_name}")
        
        # Create WhatsApp account with Meta test number
        wa = WhatsAppAccount(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            phone_number=whatsapp_number  # Meta-generated test number
        )
        db.add(wa)
        print(f"✅ Created WhatsApp account: {whatsapp_number}")
        
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
        print("  python setup_tenant.py 'My Business' '+250788999999' '+250788123456'")
        print("\nArguments:")
        print("  tenant_name: Your business name")
        print("  whatsapp_number: The Meta-generated test number")
        print("  seller_phone: Your personal WhatsApp number (to receive notifications)")
        sys.exit(1)
    
    tenant_name = sys.argv[1]
    whatsapp_number = sys.argv[2]
    seller_phone = sys.argv[3]
    
    setup_tenant(tenant_name, whatsapp_number, seller_phone)
