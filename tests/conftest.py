"""Pytest fixtures for Verk Employee Management tests."""

from pathlib import Path

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

PDF_EXPORT_TESTS_WITH_FAKE_GENERATOR = {
    "test_export_pdf_passes_monthly_vacation_days_to_template",
    "test_export_pdf_vacation_days_excludes_weekends",
}


def _playwright_chromium_available() -> bool:
    """Return whether Playwright's Chromium binary is installed."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False

    try:
        with sync_playwright() as playwright:
            return Path(playwright.chromium.executable_path).exists()
    except Exception:
        return False


def _requires_playwright_chromium(nodeid: str, test_name: str) -> bool:
    """Identify tests that launch Chromium through the PDF generator."""
    if nodeid.startswith("tests/documents/test_pdf_generator.py::"):
        return True
    if nodeid.startswith("tests/api/test_data_transfer.py::TestExportEndpoint::test_export_pdf"):
        return True
    if nodeid.startswith("tests/services/data_transfer/test_pdf_export_service.py::"):
        return test_name not in PDF_EXPORT_TESTS_WITH_FAKE_GENERATOR
    return False


def pytest_collection_modifyitems(config, items):
    """Skip Chromium-backed PDF tests when the browser binary is not installed."""
    if _playwright_chromium_available():
        return

    skip_pdf_browser = pytest.mark.skip(
        reason="Requires Playwright Chromium browser; run 'playwright install chromium'"
    )
    for item in items:
        if _requires_playwright_chromium(item.nodeid, item.name):
            item.add_marker(skip_pdf_browser)


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
