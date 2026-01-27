"""Database configuration and session management.

This module provides SQLAlchemy engine, session factory, and base model class
for the Verk Employee Management Extension.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite database path
DATABASE_URL = "sqlite:///data/employees.db"

# Create engine with SQLite-specific configuration
# check_same_thread=False is required for FastAPI async operations
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all SQLAlchemy models
Base = declarative_base()
