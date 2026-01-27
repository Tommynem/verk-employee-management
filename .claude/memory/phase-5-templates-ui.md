# Phase 5: Templates & UI

## Status

**BLOCKED ON**: Figma design transcription for machine readability

The Figma design is complete but needs to be imported/transcribed before implementation.

---

## Template Structure

Following VaWW naming conventions:

```
templates/
├── base.html                          # Already exists, may need updates
├── pages/
│   └── time_entries.html              # Full page wrapper
├── partials/
│   ├── _browser_time_entries.html     # List/table view
│   ├── _detail_time_entry.html        # Single entry detail
│   ├── _new_time_entry.html           # Create form
│   ├── _edit_time_entry.html          # Edit form
│   ├── _summary_week.html             # Weekly summary
│   └── _summary_month.html            # Monthly summary
└── components/
    └── (copy from VaWW as needed)
```

---

## VaWW Components to Copy

From `/Users/tomge/Documents/Git/vaww/the_great_rewiring/templates/web/`:

| Component | Source Path | Purpose |
|-----------|-------------|---------|
| Delete modal | `components/_modal_confirm_delete.html` | Delete confirmation |
| Discard modal | `components/_modal_confirm_discard.html` | Unsaved changes warning |
| Icon macros | `macros/_icons.html` | SVG icons |
| Base template | `base.html` | Reference for structure |

Copy command pattern:
```bash
cp /Users/tomge/Documents/Git/vaww/the_great_rewiring/templates/web/components/_modal_confirm_delete.html \
   templates/components/
```

---

## HTMX Interaction Patterns

### List View with Inline Edit

```html
<!-- _browser_time_entries.html -->
<table class="table table-zebra">
  <thead>
    <tr>
      <th>Datum</th>
      <th>Ankunft</th>
      <th>Ende</th>
      <th>Pause</th>
      <th>Stunden</th>
      <th>+/-</th>
      <th>Bemerkung</th>
      <th></th>
    </tr>
  </thead>
  <tbody id="time-entry-list">
    {% for entry in entries %}
    <tr id="time-entry-{{ entry.id }}"
        hx-get="/time-entries/{{ entry.id }}/edit"
        hx-trigger="dblclick"
        hx-target="this"
        hx-swap="outerHTML">
      <td>{{ entry.work_date.strftime('%d.%m.%Y') }}</td>
      <td>{{ entry.start_time.strftime('%H:%M') if entry.start_time else '-' }}</td>
      <td>{{ entry.end_time.strftime('%H:%M') if entry.end_time else '-' }}</td>
      <td>{{ entry.break_minutes or 0 }} min</td>
      <td>{{ "%.2f"|format(entry.actual_hours) }}</td>
      <td class="{{ 'text-success' if entry.balance >= 0 else 'text-error' }}">
        {{ "+%.2f"|format(entry.balance) if entry.balance >= 0 else "%.2f"|format(entry.balance) }}
      </td>
      <td>{{ entry.notes or '' }}</td>
      <td>
        <button class="btn btn-ghost btn-xs"
                hx-delete="/time-entries/{{ entry.id }}"
                hx-confirm="Eintrag wirklich löschen?"
                hx-target="#time-entry-{{ entry.id }}"
                hx-swap="outerHTML">
          {% call icon('trash') %}{% endcall %}
        </button>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
```

### New Entry Form

```html
<!-- _new_time_entry.html -->
<form hx-post="/time-entries"
      hx-target="#time-entry-list"
      hx-swap="afterbegin"
      class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <h2 class="card-title">Neuer Zeiteintrag</h2>

    <div class="form-control">
      <label class="label">Datum</label>
      <input type="date" name="work_date" class="input input-bordered" required
             data-flatpickr data-locale="de">
    </div>

    <div class="grid grid-cols-3 gap-4">
      <div class="form-control">
        <label class="label">Ankunft</label>
        <input type="time" name="start_time" class="input input-bordered">
      </div>
      <div class="form-control">
        <label class="label">Ende</label>
        <input type="time" name="end_time" class="input input-bordered">
      </div>
      <div class="form-control">
        <label class="label">Pause (min)</label>
        <input type="number" name="break_minutes" class="input input-bordered"
               min="0" max="480" value="30">
      </div>
    </div>

    <div class="form-control">
      <label class="label">Abwesenheit</label>
      <select name="absence_type" class="select select-bordered">
        <option value="none">Keine</option>
        <option value="vacation">Urlaub</option>
        <option value="sick">Krank</option>
        <option value="holiday">Feiertag</option>
        <option value="flex_time">Zeitausgleich</option>
      </select>
    </div>

    <div class="form-control">
      <label class="label">Bemerkung</label>
      <textarea name="notes" class="textarea textarea-bordered"></textarea>
    </div>

    <div class="card-actions justify-end">
      <button type="button" class="btn btn-ghost"
              hx-get="/time-entries" hx-target="#content">Abbrechen</button>
      <button type="submit" class="btn btn-primary">Speichern</button>
    </div>
  </div>
</form>
```

---

## Summary Display

### Weekly Summary

```html
<!-- _summary_week.html -->
<div class="stats shadow">
  <div class="stat">
    <div class="stat-title">Gearbeitet</div>
    <div class="stat-value">{{ "%.1f"|format(summary.total_actual) }}h</div>
  </div>
  <div class="stat">
    <div class="stat-title">Soll</div>
    <div class="stat-value">{{ "%.1f"|format(summary.total_target) }}h</div>
  </div>
  <div class="stat">
    <div class="stat-title">Saldo</div>
    <div class="stat-value {{ 'text-success' if summary.total_balance >= 0 else 'text-error' }}">
      {{ "+%.1f"|format(summary.total_balance) if summary.total_balance >= 0 else "%.1f"|format(summary.total_balance) }}h
    </div>
  </div>
</div>
```

---

## Flatpickr Integration

For date/time pickers with German locale:

```html
<script>
document.addEventListener('DOMContentLoaded', function() {
  flatpickr('[data-flatpickr]', {
    locale: 'de',
    dateFormat: 'd.m.Y',
    allowInput: true
  });

  flatpickr('input[type="time"]', {
    enableTime: true,
    noCalendar: true,
    dateFormat: 'H:i',
    time_24hr: true
  });
});
</script>
```

---

## Playwright E2E Tests

Location: `tests/e2e/test_time_entry_flow.py`

```python
import pytest
from playwright.sync_api import Page, expect

class TestTimeEntryFlow:
    def test_create_entry_flow(self, page: Page, live_server):
        """User can create a new time entry."""
        page.goto(f"{live_server}/time-entries")

        # Click new entry button
        page.click("text=Neuer Eintrag")

        # Fill form
        page.fill('input[name="work_date"]', '15.01.2026')
        page.fill('input[name="start_time"]', '07:00')
        page.fill('input[name="end_time"]', '15:30')
        page.fill('input[name="break_minutes"]', '30')
        page.fill('textarea[name="notes"]', 'Test entry')

        # Submit
        page.click('button[type="submit"]')

        # Verify entry appears in list
        expect(page.locator('#time-entry-list')).to_contain_text('15.01.2026')
        expect(page.locator('#time-entry-list')).to_contain_text('8.00')

    def test_edit_entry_inline(self, page: Page, live_server, db_with_entry):
        """User can edit entry by double-clicking."""
        page.goto(f"{live_server}/time-entries")

        # Double-click to edit
        page.dblclick('#time-entry-1')

        # Form should appear
        expect(page.locator('form')).to_be_visible()

    def test_delete_entry_with_confirmation(self, page: Page, live_server, db_with_entry):
        """Delete shows confirmation, then removes entry."""
        page.goto(f"{live_server}/time-entries")

        # Click delete
        page.click('#time-entry-1 button[hx-delete]')

        # Handle confirmation dialog
        page.on('dialog', lambda d: d.accept())

        # Entry should be gone
        expect(page.locator('#time-entry-1')).not_to_be_visible()
```

---

## Implementation Checklist

After Figma import:

- [ ] Copy needed VaWW components
- [ ] Create `_browser_time_entries.html`
- [ ] Create `_detail_time_entry.html`
- [ ] Create `_new_time_entry.html`
- [ ] Create `_edit_time_entry.html`
- [ ] Create `_summary_week.html`
- [ ] Create `_summary_month.html`
- [ ] Update `base.html` if needed
- [ ] Write Playwright tests
- [ ] Verify all HTMX interactions work
