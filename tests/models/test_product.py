# tests/models/test_product.py

import pytest
from app.db.models_import import Product
from app.models.tenant import Tenant
import uuid
from decimal import Decimal


def test_create_product(db_session, tenant):
    """Test basic product creation with price_per_unit."""
    product = Product(
        id="P001",
        tenant_id=tenant.id,
        name="Amashu",
        price_per_unit=Decimal("3000.00")
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    fetched = db_session.get(Product, "P001")
    assert fetched is not None
    assert fetched.name == "Amashu"
    assert fetched.price_per_unit == Decimal("3000.00")
    assert fetched.cost_per_unit is None
    assert fetched.tenant_id == tenant.id


def test_product_optional_fields(db_session, tenant):
    """Test that price_per_unit and cost_per_unit are optional."""
    product = Product(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        name="Indimu"
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    assert product.price_per_unit is None
    assert product.cost_per_unit is None


def test_product_cost_per_unit_tracking(db_session, tenant):
    """Test creation of a product with cost_per_unit for profit tracking."""
    product = Product(
        id="P007",
        tenant_id=tenant.id,
        name="Avocado",
        cost_per_unit=Decimal("500.00")
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    fetched = db_session.get(Product, "P007")
    assert fetched.cost_per_unit == Decimal("500.00")
    assert fetched.price_per_unit is None


def test_product_unique_name_per_tenant(db_session, tenant):
    """Test that a product name must be unique per tenant."""
    product1 = Product(
        id="P002",
        tenant_id=tenant.id,
        name="Banana"
    )
    product2 = Product(
        id="P003",
        tenant_id=tenant.id,
        name="Banana"  # same name, same tenant
    )

    db_session.add(product1)
    db_session.commit()

    db_session.add(product2)
    with pytest.raises(Exception):
        db_session.commit()


def test_product_relationship_to_tenant(db_session, tenant):
    """Ensure the product is linked to its tenant correctly."""
    product = Product(
        id="P004",
        tenant_id=tenant.id,
        name="Pineapple"
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    assert product.tenant.id == tenant.id
    assert product.tenant.name == tenant.name


def test_multiple_products_same_name_different_tenants(db_session):
    """Ensure same product name can exist for different tenants."""
    tenant1 = Tenant(id="T002", name="Tenant 2")
    tenant2 = Tenant(id="T003", name="Tenant 3")
    db_session.add_all([tenant1, tenant2])
    db_session.commit()

    product1 = Product(
        id="P005",
        tenant_id=tenant1.id,
        name="Amashu"
    )
    product2 = Product(
        id="P006",
        tenant_id=tenant2.id,
        name="Amashu"
    )
    db_session.add_all([product1, product2])
    db_session.commit()

    assert db_session.get(Product, "P005").tenant_id == tenant1.id
    assert db_session.get(Product, "P006").tenant_id == tenant2.id