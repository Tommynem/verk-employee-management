/**
 * Verk Employee Management - Main Application JavaScript
 *
 * Uses event delegation for HTMX-compatible dynamic content handling.
 */
(function() {
    'use strict';

    /**
     * Format time input to HH:MM format.
     * Handles various input formats: single digit, double digit, HMM, HHMM, H:MM, HH:MM
     *
     * Examples:
     *   "6" -> "06:00"
     *   "830" -> "08:30"
     *   "1630" -> "16:30"
     *   "8:30" -> "08:30"
     *
     * @param {string} value - Input time string
     * @returns {string} Formatted time string in HH:MM format
     */
    function formatTimeInput(value) {
        // Strip whitespace
        value = value.trim();

        // Empty string returns empty
        if (!value) {
            return '';
        }

        // If already in colon format, validate and normalize
        if (value.includes(':')) {
            const parts = value.split(':');
            if (parts.length === 2) {
                const hour = parseInt(parts[0], 10);
                const minute = parseInt(parts[1], 10);
                if (!isNaN(hour) && !isNaN(minute) && hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59) {
                    return String(hour).padStart(2, '0') + ':' + String(minute).padStart(2, '0');
                }
            }
            return ''; // Invalid format, clear field
        }

        // Must be numeric from here
        if (!/^\d+$/.test(value)) {
            return ''; // Invalid, clear field
        }

        const length = value.length;

        // Parse based on length
        if (length === 1 || length === 2) {
            // One or two digits: treat as hour (e.g., "6" -> "06:00", "14" -> "14:00")
            const hour = parseInt(value, 10);
            if (hour === 24) return '00:00'; // Special case
            if (hour >= 0 && hour <= 23) {
                return String(hour).padStart(2, '0') + ':00';
            }
        } else if (length === 3) {
            // Three digits: HMM format (e.g., "830" -> "08:30")
            const hour = parseInt(value[0], 10);
            const minute = parseInt(value.slice(1), 10);
            if (hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59) {
                return String(hour).padStart(2, '0') + ':' + String(minute).padStart(2, '0');
            }
        } else if (length === 4) {
            // Four digits: HHMM format (e.g., "1630" -> "16:30")
            const hour = parseInt(value.slice(0, 2), 10);
            const minute = parseInt(value.slice(2), 10);
            if (hour === 24 && minute === 0) return '00:00'; // Special case
            if (hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59) {
                return String(hour).padStart(2, '0') + ':' + String(minute).padStart(2, '0');
            }
        }

        // Invalid format, clear field
        return '';
    }

    /**
     * Event delegation for editable time entry rows
     * Handles keyboard shortcuts: Enter to save, Escape to cancel
     */
    document.addEventListener('keydown', function(event) {
        // For Enter key, require the target to be within an editable row
        if (event.key === 'Enter' && !event.shiftKey) {
            const editRow = event.target.closest('tr[data-edit-row]');
            if (editRow) {
                event.preventDefault();
                const saveBtn = editRow.querySelector('.btn-primary');
                if (saveBtn) saveBtn.click();
            }
        }
        // For Escape key, find any visible edit row (even if event target is elsewhere)
        else if (event.key === 'Escape') {
            // First check if event target is within an edit row
            let editRow = event.target.closest('tr[data-edit-row]');

            // If not, find any visible edit row on the page
            if (!editRow) {
                editRow = document.querySelector('tr[data-edit-row]');
            }

            if (editRow) {
                event.preventDefault();
                // Look for cancel button with title "Abbrechen" or aria-label "Abbrechen"
                const cancelBtn = editRow.querySelector('button[title="Abbrechen"]') ||
                                 editRow.querySelector('button[aria-label="Abbrechen"]');
                if (cancelBtn) {
                    cancelBtn.click();
                }
            }
        }
    });

    /**
     * Global keyboard shortcuts for time tracking navigation
     * Handles shortcuts when NOT in an input field to prevent conflicts
     */
    document.addEventListener('keydown', function(event) {
        // Ignore shortcuts if user is typing in an input field
        const target = event.target;
        const isInputField = target.tagName === 'INPUT' ||
                           target.tagName === 'TEXTAREA' ||
                           target.isContentEditable;

        if (isInputField) return;

        // N key: Add next day entry (trigger "Add Next Day" button)
        if (event.key === 'n' || event.key === 'N') {
            event.preventDefault();
            const addButton = document.querySelector('button[hx-get*="/time-entries/new-row"]');
            if (addButton) {
                addButton.click();
            }
        }

        // T key: Jump to today/current month
        else if (event.key === 't' || event.key === 'T') {
            event.preventDefault();
            // Navigate to time entries without month/year query params (defaults to current month)
            window.location.href = '/time-entries';
        }

        // Arrow Left: Previous month
        else if (event.key === 'ArrowLeft') {
            event.preventDefault();
            const prevButton = document.querySelector('button[aria-label="Vorheriger Monat"]');
            if (prevButton) {
                prevButton.click();
            }
        }

        // Arrow Right: Next month
        else if (event.key === 'ArrowRight') {
            event.preventDefault();
            const nextButton = document.querySelector('button[aria-label="Nächster Monat"]');
            if (nextButton) {
                nextButton.click();
            }
        }
    });

    /**
     * Event delegation for time input formatting on blur.
     * Automatically formats time inputs when user leaves the field.
     */
    document.addEventListener('blur', function(event) {
        const target = event.target;

        // Check if the blurred element is a time input field
        // Match: name="start_time", name="end_time", or name="weekday_N_start_time", "weekday_N_end_time"
        if (target.tagName === 'INPUT' &&
            (target.name === 'start_time' ||
             target.name === 'end_time' ||
             /^weekday_\d+_(start|end)_time$/.test(target.name))) {

            // Format the value
            const formatted = formatTimeInput(target.value);
            if (formatted !== target.value) {
                target.value = formatted;
            }
        }
    }, true); // Use capture phase to ensure we catch blur events

    /**
     * Toggle weekday input fields in settings page
     * Attached to window for inline event handler compatibility
     *
     * @param {number} weekday - Day index (0-6)
     * @param {boolean} enabled - Whether the day should be enabled
     */
    window.toggleWeekdayInputs = function(weekday, enabled) {
        const inputs = document.querySelectorAll(`[name^="weekday_${weekday}_"]:not([name$="_enabled"])`);
        inputs.forEach(input => {
            input.disabled = !enabled;
            if (!enabled) {
                input.value = '';
            }
        });
    };

    /**
     * Auto-suggest break time for work > 6 hours.
     * German labor law (Arbeitszeitgesetz) requires 30 min break for >6h work.
     *
     * @param {HTMLElement} editRow - The edit row element
     */
    function suggestBreakTime(editRow) {
        const startInput = editRow.querySelector('input[name="start_time"]');
        const endInput = editRow.querySelector('input[name="end_time"]');
        const breakInput = editRow.querySelector('input[name="break_minutes"]');

        if (!startInput || !endInput || !breakInput) return;

        const startTime = startInput.value;
        const endTime = endInput.value;

        // Only suggest if both times are filled and break is 0/empty
        if (!startTime || !endTime) return;
        if (breakInput.value && parseInt(breakInput.value, 10) > 0) return;

        // Parse HH:MM format
        const startParts = startTime.split(':');
        const endParts = endTime.split(':');
        if (startParts.length !== 2 || endParts.length !== 2) return;

        const startH = parseInt(startParts[0], 10);
        const startM = parseInt(startParts[1], 10);
        const endH = parseInt(endParts[0], 10);
        const endM = parseInt(endParts[1], 10);

        // Validate time values
        if (isNaN(startH) || isNaN(startM) || isNaN(endH) || isNaN(endM)) return;

        // Calculate duration in minutes
        const startMinutes = startH * 60 + startM;
        const endMinutes = endH * 60 + endM;
        const durationMinutes = endMinutes - startMinutes;

        // If > 6 hours (360 min), suggest 30 min break
        if (durationMinutes > 360) {
            breakInput.value = 30;
            // Brief visual highlight
            breakInput.classList.add('input-warning');
            setTimeout(() => breakInput.classList.remove('input-warning'), 2000);
        }
    }

    /**
     * Event delegation for time input changes to trigger break suggestion
     */
    document.addEventListener('change', function(event) {
        if (event.target.matches('[data-edit-row] input[name="start_time"], [data-edit-row] input[name="end_time"]')) {
            const editRow = event.target.closest('[data-edit-row]');
            if (editRow) {
                suggestBreakTime(editRow);
            }
        }
    });

    /**
     * Trigger break suggestion after blur event when time formatting completes
     */
    document.addEventListener('blur', function(event) {
        const target = event.target;

        // After time input formatting, check if we should suggest break time
        if (target.tagName === 'INPUT' &&
            (target.name === 'start_time' || target.name === 'end_time')) {

            const editRow = target.closest('[data-edit-row]');
            if (editRow) {
                // Small delay to ensure formatted value is set
                setTimeout(() => suggestBreakTime(editRow), 50);
            }
        }
    }, true);

    /**
     * Copy last entry's times to current edit row
     * Fetches the most recent entry's start_time, end_time, and break_minutes
     * and populates the current row's input fields
     *
     * @param {HTMLElement} button - The copy button element
     */
    window.copyLastEntry = async function(button) {
        const row = button.closest('tr');
        if (!row) return;

        try {
            const response = await fetch('/time-entries/last');

            if (!response.ok) {
                // No previous entries found or error
                if (response.status === 404) {
                    alert('Keine vorherigen Einträge gefunden');
                } else {
                    alert('Fehler beim Laden der letzten Eintragsdaten');
                }
                return;
            }

            const data = await response.json();

            // Populate the form fields
            const startTimeInput = row.querySelector('[name="start_time"]');
            const endTimeInput = row.querySelector('[name="end_time"]');
            const breakMinutesInput = row.querySelector('[name="break_minutes"]');

            if (startTimeInput && data.start_time !== null) {
                startTimeInput.value = data.start_time;
            }
            if (endTimeInput && data.end_time !== null) {
                endTimeInput.value = data.end_time;
            }
            if (breakMinutesInput && data.break_minutes !== null) {
                breakMinutesInput.value = data.break_minutes;
            }

        } catch (error) {
            console.error('Error copying last entry:', error);
            alert('Fehler beim Kopieren der letzten Eintragsdaten');
        }
    };

    /**
     * Auto-refresh time entries view when entries are created, updated, or deleted.
     * This ensures summary cards (Monatssaldo, Sollstunden, Aktuelles Zeitkonto)
     * and weekly summaries update automatically without manual page refresh.
     */
    document.body.addEventListener('timeEntryCreated', function() {
        refreshTimeEntriesView();
    });

    document.body.addEventListener('timeEntryUpdated', function() {
        refreshTimeEntriesView();
    });

    document.body.addEventListener('timeEntryDeleted', function() {
        refreshTimeEntriesView();
    });

    /**
     * Helper function to refresh the time entries content area
     */
    function refreshTimeEntriesView() {
        const contentEl = document.getElementById('time-entries-content');
        if (contentEl) {
            // Re-fetch current view to update summaries
            const url = window.location.pathname + window.location.search;
            htmx.ajax('GET', url, {target: '#time-entries-content', swap: 'innerHTML'});
        }
    }

})();
