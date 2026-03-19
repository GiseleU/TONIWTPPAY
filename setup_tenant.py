# #!/usr/bin/env python3
# """
# Setup script to create your tenant and WhatsApp account.
# Run this locally or on Render to set up your data.

# ✅ Fully aligned with:
# - phone_number (Meta human-readable)
# - phone_number_id (Meta numeric ID / webhook key)
# - Tenant existence check
# - WhatsApp account existence check
# """

# import uuid
# from app.db.session import get_db
# from app.db.models_import import *  # Populate SQLAlchemy registry
# from app.models.tenant import Tenant
# from app.models.whatsapp_account import WhatsAppAccount
# from app.core.enums import CoexistenceStatus


# def setup_tenant(
#     tenant_name: str,
#     whatsapp_number: str,       # Meta human-readable (e.g., "+15551936124")
#     phone_number_id: str,       # Meta API / webhook numeric ID (e.g., "973471879191031")
#     seller_phone: str           # Seller's personal WhatsApp number
# ):
#     """Create tenant and WhatsApp account with proper phone_number_id"""
#     db = next(get_db())

#     try:
#         # --------------------------
#         # 1️⃣ Check if WhatsApp account already exists
#         # --------------------------
#         existing_wa: WhatsAppAccount | None = db.query(WhatsAppAccount).filter(
#             WhatsAppAccount.phone_number_id == phone_number_id
#         ).first()

#         if existing_wa:
#             tenant = db.query(Tenant).filter(Tenant.id == existing_wa.tenant_id).first()
#             print(f"✅ WhatsApp account already exists: {existing_wa.phone_number}")
#             print(f"   phone_number_id: {existing_wa.phone_number_id}")
#             print(f"   Tenant: {tenant.name if tenant else 'Unknown'}")
#             return

#         # --------------------------
#         # 2️⃣ Check if tenant already exists by seller phone
#         # --------------------------
#         existing_tenant: Tenant | None = db.query(Tenant).filter(
#             Tenant.phone_number == seller_phone
#         ).first()

#         if existing_tenant:
#             tenant = existing_tenant
#             print(f"✅ Using existing tenant for seller {seller_phone}: {tenant.name}")
#         else:
#             tenant = Tenant(
#                 id=str(uuid.uuid4()),
#                 name=tenant_name,
#                 phone_number=seller_phone,
#                 coexistence_status=CoexistenceStatus.ACTIVE
#             )
#             db.add(tenant)
#             db.flush()  # Ensure tenant.id is available
#             print(f"✅ Created tenant: {tenant_name}")

#         # --------------------------
#         # 3️⃣ Create WhatsApp account for Meta number
#         # --------------------------
#         wa = WhatsAppAccount(
#             id=str(uuid.uuid4()),
#             tenant_id=tenant.id,
#             phone_number=whatsapp_number,
#             phone_number_id=phone_number_id  # ← webhook lookup key
#         )
#         db.add(wa)
#         db.commit()
#         print(f"✅ Created WhatsApp account: {wa.phone_number}")
#         print(f"   phone_number_id: {wa.phone_number_id} (webhook ready)")
#         print(f"   Tenant: {tenant.name}")

#     except Exception as e:
#         db.rollback()
#         print(f"❌ Error setting up tenant: {e}")
#         raise

#     finally:
#         db.close()


# # --------------------------
# # CLI interface
# # --------------------------
# if __name__ == "__main__":
#     import sys

#     if len(sys.argv) < 5:
#         print("Usage: python setup_tenant.py <tenant_name> <whatsapp_number> <phone_number_id> <seller_phone>")
#         print("\nExample:")
#         print("  python setup_tenant.py 'My Business' '+15551936124' '973471879191031' '+250788123456'")
#         sys.exit(1)

#     tenant_name = sys.argv[1]
#     whatsapp_number = sys.argv[2]
#     phone_number_id = sys.argv[3]
#     seller_phone = sys.argv[4]

#     setup_tenant(tenant_name, whatsapp_number, phone_number_id, seller_phone)




#!/usr/bin/env python3
"""
Setup script to create your tenant.
Run this locally or on Render to set up your data.

✅ Fully aligned with:
- Tenant: name + seller phone
- No separate WhatsApp account needed
"""

import uuid
from app.db.session import get_db
from app.db.models_import import *
from app.models.tenant import Tenant
from app.core.enums import CoexistenceStatus


def setup_tenant(
    tenant_name: str,
    seller_phone: str           # Seller's personal WhatsApp number
):
    """Create tenant if it doesn't exist"""
    db = next(get_db())

    try:
        # Check if tenant already exists by seller phone
        tenant: Tenant | None = db.query(Tenant).filter(
            Tenant.phone_number == seller_phone
        ).first()

        if tenant:
            print(f"✅ Tenant already exists for seller {seller_phone}: {tenant.name}")
            return

        # Create new tenant
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=tenant_name,
            phone_number=seller_phone,
            coexistence_status=CoexistenceStatus.ACTIVE
        )
        db.add(tenant)
        db.commit()
        print(f"✅ Created tenant: {tenant_name} (seller phone: {seller_phone})")

    except Exception as e:
        db.rollback()
        print(f"❌ Error setting up tenant: {e}")
        raise

    finally:
        db.close()


# --------------------------
# CLI interface
# --------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python setup_tenant.py <tenant_name> <seller_phone>")
        print("\nExample:")
        print("  python setup_tenant.py 'My Business' '+250788123456'")
        sys.exit(1)

    tenant_name = sys.argv[1]
    seller_phone = sys.argv[2]

    setup_tenant(tenant_name, seller_phone)