import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from app.main import app
from app.db.base import Base
from app.db.models_import import *
from app.db.session import get_db

@pytest.fixture(scope="function")
def engine():
    """Create a temporary SQLite database for each test."""
    tmp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_file.close()  # Close the file so SQLite can open it
    db_url = f"sqlite:///{tmp_file.name}"
    engine = create_engine(db_url, echo=False, future=True, connect_args={"check_same_thread": False})
    yield engine
    engine.dispose()
    if os.path.exists(tmp_file.name):
        os.remove(tmp_file.name)


@pytest.fixture(scope="function")
def db_session(engine):
    """Provide a new database session for each test function."""
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)   

@pytest.fixture
def tenant(db_session):
    """Test tenant with id='T001' matching all test payloads."""
    from app.models.tenant import Tenant
    from app.core.enums import CoexistenceStatus
    
    tenant = Tenant(
        id="T001",
        name="Test Tenant",
        phone_number="250700000001",
        coexistence_status=CoexistenceStatus.ACTIVE
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant

@pytest.fixture
def client(db_session):
    """
    Provide a TestClient that overrides get_db with the test db_session.
    Ensures the FastAPI endpoints use the same database as the test session.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

