# Testing Issues Tracker

**Testing Started**: 2026-01-28
**Status**: IN PROGRESS
**Server**: localhost:8000

## Issue Summary

| Severity | Count | Description |
|----------|-------|-------------|
| Critical | 12 | App crashes, data loss |
| Major | 16 | Feature broken, bad UX |
| Minor | 8 | Visual glitches, edge cases |

**Note**: 2 bugs (C9, C10) were removed after cross-verification - they work correctly. M9 fixed on 2026-01-29.

---

## Critical Issues

### ISSUE-C1: Silent Save Failure for Empty Tracking Values
- **Severity**: Critical
- **Page**: Settings
- **Description**: Submitting empty values for tracking settings fails silently without any user feedback
- **Steps to Reproduce**:
  1. Navigate to /settings
  2. Clear all three tracking settings fields (Wochenstunden, Erfassungsbeginn, Anfangssaldo)
  3. Click "Speichern" button
  4. Refresh the page - previous values restored
- **Expected**: Either accept empty values OR show validation error
- **Actual**: Page appears to save, no error shown, but values not persisted
- **Impact**: User confusion and potential data loss
- **Status**: OPEN

### ISSUE-C2: End Time Before Start Time Accepted
- **Severity**: Critical
- **Page**: Settings (Weekday Defaults)
- **Description**: Weekday work times can be saved with end time before start time (negative hours)
- **Steps to Reproduce**:
  1. Navigate to settings page
  2. Set Montag "Ankunft" to 17:00
  3. Set Montag "Ende" to 08:00
  4. Click "Speichern"
- **Expected**: Validation error preventing save
- **Actual**: Values accepted and saved, would calculate negative work hours
- **Impact**: Could cause incorrect time calculations, data integrity issues
- **Status**: OPEN

### ISSUE-C3: Disabling All Weekdays Doesn't Persist
- **Severity**: Critical
- **Page**: Settings (Weekday Defaults)
- **Description**: When all weekday checkboxes are unchecked and saved, all days automatically re-enable
- **Steps to Reproduce**:
  1. Navigate to settings page
  2. Uncheck all weekday checkboxes (Montag through Samstag)
  3. Click "Speichern"
  4. All checkboxes are checked again after save
- **Expected**: Disabled state should persist
- **Actual**: All days automatically re-enabled after save
- **Impact**: Impossible to configure schedule with no default work days
- **Status**: OPEN

### ISSUE-C4: Weekly Summary Shows Wrong Week
- **Severity**: Critical
- **Page**: Time Entries
- **Description**: Weekly summary always shows current real-world week, not the week being viewed
- **Code Location**: `source/api/routers/time_entries.py` lines 223-241 uses `date.today()`
- **Steps to Reproduce**:
  1. Navigate to /time-entries?month=1&year=2026
  2. Create entries for Jan 1-2
  3. Weekly summary shows "0:00h / 40:00h (-40:00h)" for current week
  4. Should show hours from the entries being viewed
- **Expected**: Weekly summary reflects the entries in the viewed month/context
- **Actual**: Always shows current week (date.today() hardcoded)
- **Impact**: Summary is misleading/useless when viewing historical months
- **Status**: OPEN

### ISSUE-C5: Non-existent Time Entry Returns JSON Instead of HTML 404
- **Severity**: Critical
- **Page**: Time Entries Detail
- **Description**: Accessing non-existent entry ID returns raw JSON, not styled 404 page
- **Steps to Reproduce**:
  1. Navigate to http://localhost:8000/time-entries/99999
- **Expected**: Styled 404 error page like other routes
- **Actual**: Returns `{"detail":"Eintrag nicht gefunden"}` as plain JSON
- **Impact**: Breaks UX when accessing invalid entry URLs
- **Status**: OPEN

### ISSUE-C6: Invalid Query Parameters Return JSON Validation Errors
- **Severity**: Critical
- **Page**: Time Entries
- **Description**: Invalid month/year params return Pydantic errors as JSON, not HTML
- **Steps to Reproduce**:
  1. Navigate to /time-entries?month=13&year=2026 (invalid month)
  2. Or /time-entries?month=abc&year=xyz (non-numeric)
- **Expected**: German error message explaining valid parameter ranges
- **Actual**: Raw JSON like `{"detail":[{"type":"less_than_equal","loc":["query","month"],...}]}`
- **Impact**: Poor UX for users with invalid URLs
- **Status**: OPEN

### ISSUE-C7: No Double-Click Protection - Creates Duplicate Entries
- **Severity**: Critical
- **Page**: Time Entries
- **Description**: Rapid clicking "Nächsten Tag hinzufügen" creates multiple entries
- **Steps to Reproduce**:
  1. Click "Nächsten Tag hinzufügen" button 5 times rapidly
  2. Observe 5 new rows created
- **Expected**: Only 1 entry created (button disabled during request)
- **Actual**: 5 duplicate entries created
- **Impact**: Data integrity issue, user confusion, accidental duplicates
- **Fix**: Add `hx-disabled-elt="this"` to button
- **Status**: OPEN

### ISSUE-C8: Mobile Touch Targets Too Small
- **Severity**: Critical
- **Page**: Time Entries (Mobile)
- **Description**: Multiple buttons fail to meet 44px minimum touch target requirement
- **Affected Elements**:
  - Absence type buttons (Urlaub, Krank, Feiertag, Gleitzeit): 33-36px × 24px
  - Row action buttons (Speichern, Abbrechen, Löschen): 29px × 24px
  - Modal close button: 29px × 29px
- **Expected**: All interactive elements should be 44px × 44px minimum
- **Actual**: Most icon buttons are 24-29px high
- **Impact**: Users struggle to tap accurately on mobile devices
- **Status**: OPEN

### ~~ISSUE-C9: Enter Key Doesn't Save in Edit Row~~ - FALSE POSITIVE
- **Status**: CLOSED - NOT A BUG
- **Cross-Verification Result**: Enter key DOES save entries correctly
- **Evidence**: Edited entry, pressed Enter, entry saved and exited edit mode
- **Note**: Original report was inaccurate

### ~~ISSUE-C10: Escape Key Doesn't Close Modals~~ - FALSE POSITIVE
- **Status**: CLOSED - NOT A BUG
- **Cross-Verification Result**: Escape key DOES close modals correctly
- **Evidence**: Opened CSV Import modal, pressed Escape, modal closed immediately
- **Note**: Original report was inaccurate

### ISSUE-C11: Last-Write-Wins Race Condition - No Conflict Detection
- **Severity**: Critical
- **Page**: Time Entries
- **Description**: Concurrent edits from multiple tabs silently overwrite each other with no conflict detection
- **Steps to Reproduce**:
  1. Open Tab 1: Edit entry, change start time to 09:00, save
  2. Tab 2 (with stale data showing 08:00): Change to 07:30, save
  3. Tab 2's save overwrites Tab 1's changes with no warning
- **Expected**: Optimistic locking via timestamp check, 409 Conflict error
- **Actual**: Silent data loss - last write wins
- **Impact**: Users unknowingly overwrite each other's work
- **Fix**: Add updated_at timestamp check before save
- **Status**: OPEN

### ISSUE-C12: Settings Race Condition - Same as Time Entries
- **Severity**: Critical
- **Page**: Settings
- **Description**: Settings page has identical race condition as time entries
- **Steps to Reproduce**:
  1. Tab 1: Change Tuesday start to 07:00, save
  2. Tab 2 (stale): Change to 09:00, save
  3. Tab 2 overwrites Tab 1
- **Expected**: Conflict detection
- **Actual**: Silent overwrite
- **Impact**: Settings randomly reverted, very confusing for users
- **Status**: OPEN

### ISSUE-C13: Gleitzeit (Flex Time) Button Does Nothing
- **Severity**: Critical
- **Page**: Time Entries
- **Description**: The "Gleitzeit" quick action button has no effect whatsoever
- **Steps to Reproduce**:
  1. Navigate to /time-entries
  2. Click on a row to enter edit mode (or on an empty day)
  3. Click the "Gleitzeit" button
- **Expected**: Entry should be marked as flex time (target=8h, balance=negative 8h)
- **Actual**: Absolutely no change - no visual feedback, no calculation change
- **Impact**: Flex time feature completely broken, users cannot track flex days
- **Status**: OPEN

### ISSUE-C14: Form Labels Missing `for` Attribute (WCAG Level A Violation)
- **Severity**: Critical (Accessibility)
- **Page**: Settings
- **Description**: Form labels are not properly associated with inputs via for/id
- **Affected Fields**: Wochenstunden, Erfassungsbeginn, Anfangssaldo
- **WCAG Violation**: 3.3.2 Labels or Instructions (Level A)
- **Impact**: Screen reader users cannot identify which label belongs to which input
- **Fix**: Add `for="field_id"` to each `<label>` element
- **Status**: OPEN

---

## Major Issues

### ISSUE-M1: Invalid Time Values Accepted (Data Integrity)
- **Severity**: Major
- **Page**: Time Entries
- **Description**: Backend accepts invalid time values without validation
- **Steps to Reproduce**:
  1. Add new time entry
  2. Enter "99:99" as start time or "25:00" as end time
  3. Click "Speichern"
  4. Entry is saved with empty time fields
- **Expected**: Validation error message, entry rejected
- **Actual**: Entry saved with null/empty times
- **Impact**: Data integrity issue - invalid data can be persisted
- **Status**: OPEN

### ISSUE-M2: No Real-Time Calculation in Edit Mode
- **Severity**: Major
- **Page**: Time Entries
- **Description**: Work hours are not recalculated in real-time when editing time fields
- **Steps to Reproduce**:
  1. Click on existing time entry to edit
  2. Change the end time (e.g., 16:30 to 17:00)
  3. Observe "Arbeitsstunden Real" still shows old value
- **Expected**: Real-time calculation as user types
- **Actual**: Calculation only happens on save
- **Impact**: Users can't see effect of changes before saving
- **Status**: OPEN

### ISSUE-M3: No User Feedback for Invalid Date Format
- **Severity**: Major
- **Page**: Settings (Tracking)
- **Description**: Flatpickr throws console warning for invalid dates but no user-facing error
- **Steps to Reproduce**:
  1. Navigate to settings page
  2. Type "invalid-date" in Erfassungsbeginn field
  3. Click "Speichern"
- **Expected**: User-visible validation error message
- **Actual**: Console warning only, field clears silently
- **Impact**: Poor UX - users don't understand why input was rejected
- **Status**: OPEN

### ISSUE-M4: No Error Message When Weekday Save Fails
- **Severity**: Major
- **Page**: Settings (Weekday Defaults)
- **Description**: When weekday defaults validation fails, no error message is shown
- **Steps to Reproduce**:
  1. Navigate to settings page
  2. Set Montag "Pause (Min.)" field to 9999
  3. Click "Speichern"
- **Expected**: User-visible error message explaining validation failure
- **Actual**: Silent failure, input shows 9999 but table still shows old value
- **Impact**: User confusion - appears saved but was rejected
- **Status**: OPEN

### ISSUE-M5: Inconsistent Terminology in Monthly Summary Cards
- **Severity**: Major
- **Page**: Time Entries
- **Description**: Third summary card changes label based on whether viewing current month
- **Steps to Reproduce**:
  1. Navigate to January 2026 (current) - shows "Aktuelles Zeitkonto" / "Überstunden"
  2. Navigate to December 2025 (past) - shows "Endsaldo" / "Dezember 2025"
- **Expected**: Consistent terminology across all months
- **Actual**: Different labels depending on viewing context
- **Impact**: Confusing UX, inconsistent interface
- **Status**: OPEN

### ISSUE-M6: Import Month Mismatch - Poor Error Handling
- **Severity**: Major
- **Page**: Time Entries (Import Modal)
- **Description**: Importing CSV with entries from different month results in cryptic HTTP 422 error
- **Steps to Reproduce**:
  1. Navigate to December 2025
  2. Click "CSV Import"
  3. Upload CSV containing January 2026 entries
  4. Click "Importieren"
- **Expected**: Clear error message explaining month mismatch or auto-navigate
- **Actual**: HTTP 422 error, generic "Validierungsfehler" toast, no explanation
- **Impact**: User has no idea what went wrong
- **Status**: OPEN

### ISSUE-M7: Import Fails Silently with "Skip Existing" for Duplicate Data
- **Severity**: Major
- **Page**: Time Entries (Import Modal)
- **Description**: When importing CSV where all entries exist and "skip existing" is checked, HTTP 422 instead of success
- **Steps to Reproduce**:
  1. Navigate to January 2026 with existing entries
  2. Click "CSV Import"
  3. Upload same CSV with those entries
  4. Check "Vorhandene Einträge überspringen"
  5. Click "Importieren"
- **Expected**: Success message "0 imported, X skipped"
- **Actual**: HTTP 422 error, no feedback
- **Impact**: Confusing error handling for valid user action
- **Status**: OPEN

### ISSUE-M8: Year Boundary Navigation Shows "[object Object]"
- **Severity**: Major
- **Page**: Time Entries
- **Description**: Navigating beyond year boundaries (2020/2100) causes HTMX error and displays "[object Object]"
- **Steps to Reproduce**:
  1. Navigate to /time-entries?month=12&year=2100
  2. Click "Nächster Monat" button
  3. OR navigate to month=1&year=2020 and click "Vorheriger Monat"
- **Expected**: Buttons disabled at boundaries, or graceful error message
- **Actual**: HTMX 422 error, page displays "[object Object]"
- **Impact**: Confusing error state that breaks navigation UX
- **Fix**: Disable navigation buttons at year boundaries
- **Status**: OPEN

### ISSUE-M9: No Unsaved Changes Warning
- **Severity**: Major
- **Page**: Time Entries
- **Description**: Navigating away while editing does NOT show confirmation dialog
- **Steps to Reproduce**:
  1. Click on a time entry to edit
  2. Modify the notes field
  3. Click "Einstellingen" link
  4. Page navigates away without warning
- **Expected**: Confirmation dialog: "Sie haben ungespeicherte Änderungen"
- **Actual**: No warning, data lost silently
- **Impact**: User data loss, poor UX
- **Fix**: Implement JavaScript dirty state tracking with beforeunload handler
- **Status**: FIXED (2026-01-29)
- **Solution**: Added JavaScript dirty state tracking in `_browser_time_entries.html`
  - `beforeunload` event warns on browser navigation
  - `htmx:confirm` event warns on HTMX navigation
  - `input` event tracks field changes
  - `htmx:afterSettle` captures original values and clears state
  - `htmx:beforeRequest` clears state on save/cancel

### ISSUE-M10: Export Endpoint Validation Errors Return JSON
- **Severity**: Major
- **Page**: Time Entries (Export)
- **Description**: Invalid format or month params in export URL return JSON errors
- **Steps to Reproduce**:
  1. Navigate to /time-entries/export?month=1&year=2026&format=invalid
  2. Or /time-entries/export?month=99&year=2026&format=csv
- **Expected**: User-friendly HTML error page
- **Actual**: JSON error responses
- **Impact**: Export links with typos show raw JSON
- **Status**: OPEN

### ISSUE-M11: No Horizontal Scroll Indicator on Mobile Table
- **Severity**: Major
- **Page**: Time Entries (Mobile)
- **Description**: Table requires horizontal scroll on mobile but no visual indicator exists
- **Screen Sizes Affected**: 320px, 375px
- **Measurements**: scrollWidth 1230px vs clientWidth 991px (at 375px viewport)
- **Expected**: Visual affordance (fade/gradient) to indicate more content
- **Actual**: No indication that content continues beyond viewport
- **Impact**: Users may not realize they can scroll to access action buttons
- **Status**: OPEN

### ISSUE-M12: Header Navigation Text Cutoff at 320px
- **Severity**: Major
- **Page**: All (Header)
- **Description**: At very small screen sizes, "Zeiterfassung" text appears truncated/overlapping
- **Screen Size Affected**: 320px
- **Expected**: Text should wrap, truncate with ellipsis, or use icons only
- **Actual**: Text cramped and may overlap
- **Status**: OPEN

### ISSUE-M13: Stale Data Displayed After Concurrent Updates
- **Severity**: Major
- **Page**: Time Entries
- **Description**: After one tab saves changes, other tabs show stale data with no indication
- **Steps to Reproduce**:
  1. Tab 1 saves entry with value X
  2. Tab 2 still shows old value, no refresh indicator
  3. Month balances diverge between tabs
- **Expected**: Staleness indicator or auto-refresh
- **Actual**: Completely different data in each tab, no warning
- **Impact**: Users may make decisions based on incorrect data
- **Status**: OPEN

### ISSUE-M14: Delete HTMX Error When Entry in Edit Mode
- **Severity**: Major
- **Page**: Time Entries
- **Description**: Delete fails with HTMX error when entry is being edited
- **Steps to Reproduce**:
  1. Entry is in edit mode
  2. Click "Löschen" button
  3. Confirm delete in modal
- **Expected**: Successful deletion or clear error message
- **Actual**: HTMX targetError, entry not deleted, modal stuck
- **Console Error**: `htmx:targetError`
- **Impact**: Delete silently fails
- **Status**: OPEN

### ISSUE-M15: Confusing Actual Hours Display for Vacation/Sick
- **Severity**: Major
- **Page**: Time Entries
- **Description**: When Vacation or Sick is applied to a day, the "Actual" column shows confusing values
- **Steps to Reproduce**:
  1. Click "Urlaub" or "Krank" on a day
  2. Observe the "Arbeitsstunden Real" column shows "-0:30h"
  3. But "+/-" column correctly shows "+0:00" (8h credited)
- **Expected**: Actual column should show "8:00h" (credited hours) or indicate absence
- **Actual**: Shows "-0:30h" (negative from break deduction) which doesn't match the balance
- **Impact**: UX is confusing - math doesn't appear to add up visually
- **Status**: OPEN

### ISSUE-M16: Date Picker Year Navigation Broken
- **Severity**: Major
- **Page**: Settings (Flatpickr)
- **Description**: Year spinbutton doesn't update calendar when typed
- **Steps to Reproduce**:
  1. Click date field to open Flatpickr calendar
  2. Type a new year (e.g., "2025") in year spinbutton
  3. Calendar doesn't update to show 2025 dates
  4. Selecting month dropdown resets year to original value
- **Expected**: Calendar should update when year is changed
- **Actual**: Year spinbutton value changes but calendar stays on old year
- **Impact**: Users cannot navigate years effectively
- **Status**: OPEN

### ISSUE-M17: Invalid Date Input Accepted Without Validation
- **Severity**: Major
- **Page**: Settings (Flatpickr)
- **Description**: Invalid dates can be typed and are mangled without error
- **Steps to Reproduce**:
  1. Type "99.99.9999" in date field
  2. Flatpickr parses to nonsensical date (e.g., "09.03.0007")
  3. No error message shown
- **Expected**: Validation error, reject invalid input
- **Actual**: Invalid dates accepted and mangled
- **Impact**: Data quality issue, user confusion
- **Status**: OPEN

---

## Minor Issues

### ISSUE-m1: Inconsistent Calculation Display in Edit Mode
- **Severity**: Minor
- **Page**: Time Entries
- **Description**: +/- column shows different values in edit vs view mode
- **Steps to Reproduce**:
  1. Create entry with 8:00h work on regular day (Soll: 6:24h)
  2. View mode shows: +1:36
  3. Click to edit
  4. Edit mode shows: +0:00 and Soll changes (6:24h -> 8:00h)
- **Expected**: Consistent display in both modes
- **Actual**: Different values shown
- **Status**: OPEN

### ISSUE-m2: Duplicate Note Text Display
- **Severity**: Minor
- **Page**: Time Entries
- **Description**: Note text appears duplicated in "Abwesenheit / Bemerkung" column
- **Steps to Reproduce**:
  1. Create entry with note text
  2. Save entry
  3. Observe note appears twice in the cell
- **Expected**: Note appears once
- **Actual**: Note text duplicated
- **Status**: OPEN

### ISSUE-m3: Negative Hours Accepted for Initial Balance (Verify Intent)
- **Severity**: Minor (may be intentional)
- **Page**: Settings (Tracking)
- **Description**: Negative values for Anfangssaldo are accepted and saved
- **Steps to Reproduce**:
  1. Navigate to settings page
  2. Enter "-50" in "Anfangssaldo (Stunden)" field
  3. Click "Speichern"
- **Note**: May be intentional to allow overtime debt
- **Impact**: Should verify if this is desired behavior
- **Status**: OPEN - NEEDS CLARIFICATION

### ISSUE-m4: Draft Indicator Missing on Empty Months
- **Severity**: Minor
- **Page**: Time Entries
- **Description**: Empty months don't show any status badge, unlike months with entries
- **Steps to Reproduce**:
  1. Navigate to February 2026 (empty month)
  2. Observe month header shows "Februar 2026" with NO badge
  3. Compare to January 2026 which shows "Entwurf" badge
- **Expected**: Consistent badge behavior across all months
- **Actual**: Empty months have no badge
- **Status**: OPEN

### ISSUE-m5: No Client-Side Validation for File Selection
- **Severity**: Minor
- **Page**: Time Entries (Import Modal)
- **Description**: Import button may be clickable without selecting a file first
- **Expected**: Disable "Importieren" button until file selected OR show error
- **Actual**: Likely no client-side validation
- **Status**: OPEN - NEEDS VERIFICATION

### ISSUE-m6: No Edit Mode Locking Indicator
- **Severity**: Minor
- **Page**: Time Entries
- **Description**: Multiple tabs can edit same entry simultaneously with no warning
- **Steps to Reproduce**:
  1. Tab 1: Start editing entry
  2. Tab 2: Also start editing same entry
  3. No indication that another tab is editing
- **Expected**: Warning about concurrent editing
- **Actual**: No restrictions or warnings
- **Note**: Combined with C11/C12, this creates significant data loss risk
- **Status**: OPEN

### ISSUE-m7: No Visual Feedback for Active Absence Type
- **Severity**: Minor
- **Page**: Time Entries
- **Description**: After clicking an absence button (Urlaub, Krank, etc.), no visual indication it's active
- **Expected**: Button should show active/selected state (highlighted, different color)
- **Actual**: All buttons look the same regardless of which absence type is set
- **Impact**: Users can't tell which absence type is currently applied
- **Status**: OPEN

### ISSUE-m8: Draft Submission Workflow Incomplete
- **Severity**: Minor (or design decision)
- **Page**: Time Entries
- **Description**: "Entwurf" badge shows on months with entries, but no way to submit/finalize
- **Expected**: Button to mark month as "Abgegeben" (Submitted)
- **Actual**: No submission functionality found
- **Note**: May be intentional if submission happens outside this app
- **Status**: OPEN - NEEDS CLARIFICATION

---

## Testing Coverage

### Pages Tested

- [x] Home / Time Entries (`/time-entries`) - TESTED 2026-01-28
- [x] Settings (`/settings`) - TESTED 2026-01-28
- [x] Weekly Summary - TESTED 2026-01-28 (CRITICAL BUG FOUND)
- [x] Monthly Summary - TESTED 2026-01-28
- [x] Data Import - TESTED 2026-01-28 (BUGS FOUND)
- [x] PDF Export - TESTED 2026-01-28 (WORKING)

### Functionality Tested

- [x] Create time entry
- [x] Edit time entry
- [x] Delete time entry
- [x] Edit time entry inline (row edit)
- [x] Week navigation (partially - week summary bug found)
- [x] Month navigation (BUG: year boundaries break)
- [x] Weekday defaults settings (BUGS: validation, persistence)
- [x] Tracking settings (BUGS: silent failures)
- [x] CSV import (BUGS: error handling)
- [x] PDF export (WORKING)
- [x] Error handling (404, 500) - BUGS: JSON instead of HTML
- [x] Form validation (BUGS: XSS safe but missing feedback)
- [x] HTMX interactions (BUGS: double-click, no dirty warning)

### Edge Cases Tested

- [x] Empty database state (WORKING)
- [x] Invalid form inputs (BUGS: accepted in some cases)
- [x] Date boundary conditions (BUGS: year boundaries)
- [x] Large number entries (PASS - 31 entries, <1s response times)
- [x] Special characters in inputs (XSS safe, Unicode safe)
- [x] Concurrent edits (CRITICAL: race conditions, no conflict detection)
- [x] Mobile responsiveness (CRITICAL: touch targets, MAJOR: scroll indicator)

### Keyboard/Accessibility Tested

- [x] Documented shortcuts (N, T, arrows work; Enter broken)
- [x] Escape key (works in edit row, broken for modals)
- [x] Tab navigation (WORKING)
- [x] Focus indicators (WORKING)

### Security Tested

- [x] XSS (PASS - Jinja2 auto-escaping working)
- [x] SQL Injection (PASS - SQLAlchemy ORM protected)
- [x] Input validation (PARTIAL - some boundaries not enforced)
- [x] File upload restrictions (PARTIAL - client-side only)

---

## Testing Log

### Session 1 - 2026-01-28

**Status**: ONGOING
**Server**: localhost:8000 (running)
**Agents Deployed**: 8

**Testing Phases Completed**:
1. Time Entries CRUD - Found validation and UX issues
2. Settings Page - Found critical persistence bugs
3. Summaries - Found critical weekly summary bug
4. Data Import/Export - Found import error handling issues
5. Error Pages - Found JSON/HTML inconsistency
6. Security/Validation - XSS/SQLi safe, validation gaps
7. Mobile Responsiveness - Critical touch target issues
8. Keyboard Shortcuts - Working correctly (cross-verified)
9. Concurrent Edits - Critical race condition bugs
10. Stress Test - PASS (31 entries, <1s response, no issues)
11. URL/Deep Link Testing - PASS (good URL handling)
12. Absence Type Testing - Found C13 (Gleitzeit broken)
13. Browser Navigation - PASS (excellent HTMX/history integration)
14. Accessibility Testing - Found C14, M16, M17 (WCAG violations, date picker issues)

**Summary** (after cross-verification):
- **Critical Issues**: 12 (C14 added - accessibility)
- **Major Issues**: 17 (M16, M17 added - date picker)
- **Minor Issues**: 8
- **TOTAL**: 37 verified issues

**Cross-Verification Results**:
- C4 (Weekly summary wrong week): **VERIFIED**
- C7 (Double-click duplicates): **VERIFIED**
- C9 (Enter doesn't save): **FALSE POSITIVE** - works correctly
- C10 (Escape doesn't close): **FALSE POSITIVE** - works correctly
- M1 (Invalid times accepted): **VERIFIED**

**Key Findings**:
- Security is solid (XSS, SQLi protected)
- **CRITICAL**: Race conditions - no conflict detection on concurrent edits
- Validation feedback consistently poor
- Mobile touch targets need fixing before deployment
- Keyboard shortcuts: N, T, arrows, Enter, Escape all work correctly
- Error handling returns JSON instead of HTML in many cases
- Delete HTMX error when entry in edit mode

