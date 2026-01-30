"""Test error handling for browser and API requests.

Tests verify that browser requests (Accept: text/html) receive HTML error pages
while API requests (Accept: application/json) receive JSON error responses.

These tests follow TDD RED phase - they should FAIL until proper error handling
is implemented with content negotiation.

Issues covered:
- C5: Non-existent time entry returns JSON instead of HTML 404
- C6: Invalid query parameters return JSON validation errors
- M10: Export endpoint validation errors return JSON
"""

from tests.factories import TimeEntryFactory


class TestNonExistentTimeEntry:
    """Test C5: Non-existent time entry error handling.

    Issue: GET /time-entries/99999 returns raw JSON instead of HTML 404 for browser requests.
    Expected: Browser requests should receive HTML 404 page.
    """

    def test_browser_request_nonexistent_entry_returns_html_404(self, client, db_session):
        """Browser request for non-existent time entry should return HTML 404 page."""
        # Simulate browser request with Accept: text/html header
        response = client.get("/time-entries/99999", headers={"Accept": "text/html"})

        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        # Should contain German error message
        assert "nicht gefunden" in response.text.lower()
        # Should NOT be raw JSON
        assert not response.text.startswith("{")

    def test_browser_request_with_htmx_nonexistent_entry_returns_html_404(self, client, db_session):
        """HTMX request for non-existent time entry should return HTML 404 partial."""
        # Simulate HTMX request (browser context but partial update)
        response = client.get(
            "/time-entries/99999",
            headers={
                "Accept": "text/html",
                "HX-Request": "true",
            },
        )

        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        # Should contain German error message
        assert "nicht gefunden" in response.text.lower()
        # Should be HTML partial, not JSON
        assert not response.text.startswith("{")

    def test_api_request_nonexistent_entry_returns_json_404(self, client, db_session):
        """API request for non-existent time entry should return JSON 404."""
        # Simulate API request with Accept: application/json header
        response = client.get("/time-entries/99999", headers={"Accept": "application/json"})

        assert response.status_code == 404
        # API requests should get JSON
        assert "application/json" in response.headers["content-type"]
        json_data = response.json()
        assert "detail" in json_data
        assert "nicht gefunden" in json_data["detail"].lower()


class TestInvalidQueryParameters:
    """Test C6: Invalid query parameter error handling.

    Issue: GET /time-entries?month=13 returns raw JSON Pydantic validation error.
    Expected: Browser requests should receive HTML error page or HTMX-friendly response.
    """

    def test_browser_request_invalid_month_returns_html_error(self, client, db_session):
        """Browser request with invalid month (>12) should return HTML error page."""
        # month=13 exceeds valid range (1-12)
        response = client.get("/time-entries?month=13&year=2026", headers={"Accept": "text/html"})

        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        # Should NOT be raw JSON
        assert not response.text.startswith("{")
        # Should contain error information
        assert "monat" in response.text.lower() or "ungültig" in response.text.lower()

    def test_browser_request_invalid_month_zero_returns_html_error(self, client, db_session):
        """Browser request with invalid month (0) should return HTML error page."""
        # month=0 is below valid range (1-12)
        response = client.get("/time-entries?month=0&year=2026", headers={"Accept": "text/html"})

        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        assert not response.text.startswith("{")

    def test_browser_request_invalid_month_string_returns_html_error(self, client, db_session):
        """Browser request with non-numeric month should return HTML error page."""
        # month=abc is not a valid integer
        response = client.get("/time-entries?month=abc&year=2026", headers={"Accept": "text/html"})

        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        assert not response.text.startswith("{")

    def test_browser_request_invalid_year_string_returns_html_error(self, client, db_session):
        """Browser request with non-numeric year should return HTML error page."""
        # year=xyz is not a valid integer
        response = client.get("/time-entries?month=1&year=xyz", headers={"Accept": "text/html"})

        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        assert not response.text.startswith("{")

    def test_htmx_request_invalid_month_returns_html_partial(self, client, db_session):
        """HTMX request with invalid month should return HTML error partial."""
        response = client.get(
            "/time-entries?month=13&year=2026",
            headers={
                "Accept": "text/html",
                "HX-Request": "true",
            },
        )

        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        assert not response.text.startswith("{")

    def test_api_request_invalid_month_returns_json_error(self, client, db_session):
        """API request with invalid month should return JSON validation error."""
        response = client.get("/time-entries?month=13&year=2026", headers={"Accept": "application/json"})

        assert response.status_code == 422
        # API requests should get JSON
        assert "application/json" in response.headers["content-type"]
        json_data = response.json()
        # FastAPI validation errors have 'detail' field
        assert "detail" in json_data


class TestExportValidationErrors:
    """Test M10: Export endpoint validation error handling.

    Issue: GET /export?format=invalid returns raw JSON validation error.
    Expected: Browser requests should receive HTML error page.
    """

    def test_browser_request_invalid_export_format_returns_html_error(self, client, db_session):
        """Browser request with invalid export format should return HTML error page."""
        # Create a time entry so month/year are valid
        entry = TimeEntryFactory.build(user_id=1)
        db_session.add(entry)
        db_session.commit()

        # format=invalid is not 'csv' or 'pdf'
        response = client.get(
            f"/time-entries/export?month={entry.work_date.month}&year={entry.work_date.year}&format=invalid",
            headers={"Accept": "text/html"},
        )

        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        # Should NOT be raw JSON
        assert not response.text.startswith("{")
        # Should contain error about format
        assert "format" in response.text.lower()

    def test_browser_request_invalid_export_month_returns_html_error(self, client, db_session):
        """Browser request with invalid month (>12) should return HTML error page."""
        # month=99 exceeds valid range (1-12)
        response = client.get("/time-entries/export?month=99&year=2026&format=csv", headers={"Accept": "text/html"})

        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        assert not response.text.startswith("{")

    def test_browser_request_invalid_export_month_zero_returns_html_error(self, client, db_session):
        """Browser request with invalid month (0) should return HTML error page."""
        # month=0 is below valid range (1-12)
        response = client.get("/time-entries/export?month=0&year=2026&format=csv", headers={"Accept": "text/html"})

        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        assert not response.text.startswith("{")

    def test_htmx_request_invalid_export_format_returns_html_partial(self, client, db_session):
        """HTMX request with invalid export format should return HTML error partial."""
        response = client.get(
            "/time-entries/export?month=1&year=2026&format=invalid",
            headers={
                "Accept": "text/html",
                "HX-Request": "true",
            },
        )

        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        assert not response.text.startswith("{")

    def test_api_request_invalid_export_format_returns_json_error(self, client, db_session):
        """API request with invalid export format should return JSON error."""
        response = client.get(
            "/time-entries/export?month=1&year=2026&format=invalid", headers={"Accept": "application/json"}
        )

        assert response.status_code == 422
        # API requests should get JSON
        assert "application/json" in response.headers["content-type"]
        json_data = response.json()
        assert "detail" in json_data
        # Should contain German error message about format
        assert "format" in str(json_data["detail"]).lower()

    def test_api_request_invalid_export_month_returns_json_error(self, client, db_session):
        """API request with invalid month should return JSON validation error."""
        response = client.get(
            "/time-entries/export?month=99&year=2026&format=csv", headers={"Accept": "application/json"}
        )

        assert response.status_code == 422
        assert "application/json" in response.headers["content-type"]
        json_data = response.json()
        assert "detail" in json_data
