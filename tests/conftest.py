# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db import models_import

# -----------------------------
# Database Engine & Session
# -----------------------------

@pytest.fixture(scope="session")
def engine():
    """Create a temporary in-memory SQLite database for all tests."""
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    return engine

@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables before tests and drop after all tests are done."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine, tables):
    """Provide a new database session for each test function."""
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    finally:
        session.rollback()
        session.close()