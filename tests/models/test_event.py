# tests/models/test_event.py
import pytest
from app.db.models_import import Tenant, Event
from app.core.enums import ActorType, EventType
import uuid

def test_create_event(db_session):
    # Create tenant
    tenant = Tenant(id=str(uuid.uuid4()), name="Tenant 1")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    # Create an event linked only to tenant
    event_id = str(uuid.uuid4())
    event = Event(
        id=event_id,
        tenant_id=tenant.id,
        event_type=EventType.ORDER_CREATED,
        actor=ActorType.SYSTEM,
        visible_to_customer=True,
        payload={"note": "Test event"},
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    # Assertions
    assert event.id == event_id
    assert event.tenant.id == tenant.id
    assert event.visible_to_customer is True
    assert event.payload["note"] == "Test event"