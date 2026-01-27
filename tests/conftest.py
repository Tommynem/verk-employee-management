"""Pytest fixtures for Verk Employee Management tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from source.api.dependencies import get_db
from source.database import Base

# Test database - in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"


def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable SQLite foreign key constraints.

    Args:
        dbapi_connection: Raw SQLite connection.
        connection_record: SQLAlchemy connection record.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="function")
def test_engine():
    """Create test database engine.

    Returns:
        SQLAlchemy engine with in-memory SQLite database.

    Note:
        Creates all tables before yield, drops all after test completes.
        Enables foreign key constraints for SQLite.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", _set_sqlite_pragma)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create database session for testing.

    Args:
        test_engine: Test database engine fixture.

    Yields:
        Database session for test execution.

    Note:
        Session is rolled back after test completes to ensure test isolation.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database override.

    Args:
        db_session: Test database session fixture.

    Yields:
        TestClient instance configured to use test database.

    Note:
        Automatically overrides get_db dependency and clears overrides after test.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
