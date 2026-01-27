"""FastAPI dependencies for database sessions and other injectable services."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from source.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Provide database session, ensuring proper cleanup.

    Yields:
        Database session for the request lifecycle.

    Note:
        Session is automatically closed after request completes.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_current_user_id() -> int:
    """Get current user ID from session/auth.

    MVP: Returns hardcoded test user ID.
    Future: Integrate with VaWW authentication.

    Returns:
        Current user's ID (hardcoded to 1 for MVP).
    """
    return 1
