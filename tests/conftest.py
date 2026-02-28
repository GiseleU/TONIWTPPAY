# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db import models_import
from app.db.session import get_db


# -----------------------------
# Database Engine & Session
# -----------------------------

@pytest.fixture(scope="function")
def engine():
    """Create a temporary SQLite database for each test."""
    import tempfile
    db_file = tempfile.mktemp(suffix='.db')
    engine = create_engine(f"sqlite:///{db_file}", echo=False, future=True, connect_args={"check_same_thread": False})
    yield engine
    import os
    if os.path.exists(db_file):
        os.remove(db_file)

@pytest.fixture(scope="function")
def db_session(engine):
    """Provide a new database session for each test function."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.begin()
    try:
        yield session
    finally:
        session.rollback()
        session.close()



@pytest.fixture
def client(db_session):
    """
    Provide a TestClient that overrides get_db with the test db_session.
    """
    # Override the dependency
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()