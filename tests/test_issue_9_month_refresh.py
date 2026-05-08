"""Regression tests for GH issue #9.

Saving an entry after HTMX month navigation must not refresh a stale month.
"""

from datetime import date

from tests.factories import TimeEntryFactory


def test_time_entries_container_does_not_embed_stale_create_refresh_url(client, db_session):
    """The full page wrapper must not keep an initial month-specific refresh URL."""
    entry = TimeEntryFactory.build(user_id=1, work_date=date(2026, 3, 15))
    db_session.add(entry)
    db_session.commit()

    response = client.get("/time-entries?month=3&year=2026")

    assert response.status_code == 200
    assert '<div id="time-entries-content">' in response.text
    assert 'hx-trigger="timeEntryCreated from:body"' not in response.text
    assert 'hx-get="/time-entries?month=3&year=2026"' not in response.text


def test_entry_refresh_uses_current_browser_url():
    """The JS refresh path should follow the pushed URL after month navigation."""
    with open("static/js/app.js", encoding="utf-8") as app_js:
        source = app_js.read()

    assert "window.location.pathname + window.location.search" in source
    assert "htmx.ajax('GET', url, {target: '#time-entries-content', swap: 'innerHTML'})" in source
