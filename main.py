"""Entry point for Verk Employee Management application.

Run with: uvicorn main:app --reload
"""

from source.api.app import app

__all__ = ["app"]
