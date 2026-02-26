# # Engine/ Session factory and dependencies

# """
# Database session management

# Phase 0 responsibilities:
# - Create SQLAlchemy engine
# - Provide session factory
# - Provide FastAPI dependency for DB sessions
# """

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, Session

# from app.core.config import settings

# # ---- Engine ----
# engine = create_engine(
#     settings.DATABASE_URL,
#     pool_pre_ping=True,
#     future=True,
# )

# # ---- Session factory ----
# SessionLocal = sessionmaker(
#     bind=engine,
#     autoflush=False,
#     autocommit=False,
#     expire_on_commit=False,
#     class_=Session,
# )

# # ---- FastAPI dependency ----
# def get_db() -> Session:
#     """
#     Yields a database session and guarantees cleanup.
#     """
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()



"""
Database session management

Phase 0 responsibilities:
- Create SQLAlchemy engine
- Provide session factory
- Provide FastAPI dependency for DB sessions
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# ---- Engine ----
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

# ---- Session factory ----
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)

# ---- FastAPI dependency ----
def get_db() -> Generator[Session, None, None]:
    """
    Yields a database session and guarantees cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()