# Zeiterfassung Monthly View - Design Specification

**Source**: Figma Design
**Document Version**: 1.0
**Created**: 2025-01-27
**Tech Stack**: FastAPI, Jinja2, HTMX, Tailwind CSS, daisyUI

---

## 1. Overview

This specification defines the monthly time tracking view ("Zeiterfassung") that displays an employee's work time entries for a selected month. The view includes summary statistics cards, a detailed time entry table, and actions for adding new entries.

**Note**: The navigation/menu bar is NOT part of this spec - the existing application navigation will be used.

---

## 2. Page Layout Structure

### 2.1 Overall Container

```
+------------------------------------------------------------------+
|  [Month Navigation]                                               |
|  < Dezember 2025 >                                                |
+------------------------------------------------------------------+
|  [Summary Cards Row - 3 cards]                                    |
|  +----------------+  +----------------+  +-------------------+    |
|  | Monatssaldo    |  | Sollstunden    |  | Aktuelles         |    |
|  | 149:38h        |  | 147:12h        |  | Zeitkonto         |    |
|  | Ist-Stunden    |  | Pro Monat      |  | +19:30h           |    |
|  +----------------+  +----------------+  | Überstunden       |    |
|                                          +-------------------+    |
+------------------------------------------------------------------+
|  [Time Entry Table - Full Width Card]                             |
|  +--------------------------------------------------------------+ |
|  | Table Header (dark background)                                | |
|  | Table Body (zebra striped rows)                               | |
|  | "Add Next Day" Row (highlighted)                              | |
|  | Footer Summary Rows (green tinted)                            | |
|  +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

### 2.2 Spacing & Margins

- Page padding: `p-6` (24px)
- Gap between month nav and cards: `mt-6` (24px)
- Gap between cards and table: `mt-6` (24px)
- Card internal padding: `p-6`

---

## 3. Month Navigation Component

### 3.1 Structure

```html
<div class="flex items-center gap-3 mb-6">
    <button class="btn btn-ghost btn-square">
        <!-- Left chevron icon -->
    </button>
    <h2 class="text-2xl font-medium text-base-content">
        {{ month_name }} {{ year }}
    </h2>
    <button class="btn btn-ghost btn-square">
        <!-- Right chevron icon -->
    </button>
</div>
```

### 3.2 HTMX Behavior

| Element | Action | Endpoint | Target |
|---------|--------|----------|--------|
| Left button | `hx-get` | `/time-entries?month={prev_month}&year={prev_year}` | `#main-content` |
| Right button | `hx-get` | `/time-entries?month={next_month}&year={next_year}` | `#main-content` |

### 3.3 Display Format

- Month name in German: "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"
- Year as 4-digit number
- Example: "Dezember 2025"

---

## 4. Summary Cards Component

### 4.1 Card Layout

Three cards in a responsive row:
```html
<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <!-- Card 1: Monatssaldo -->
    <!-- Card 2: Sollstunden -->
    <!-- Card 3: Aktuelles Zeitkonto -->
</div>
```

### 4.2 Individual Card Structure

```html
<div class="card bg-base-100 shadow-md border border-base-300 rounded-lg">
    <div class="card-body p-6">
        <p class="text-sm text-base-content/70">{{ label }}</p>
        <p class="text-3xl font-normal {{ value_color }}">{{ value }}</p>
        <p class="text-xs text-base-content/50">{{ subtitle }}</p>
    </div>
</div>
```

### 4.3 Card Definitions

| Card | Label | Value Source | Subtitle | Value Color |
|------|-------|--------------|----------|-------------|
| 1 | "Monatssaldo" | `summary.total_actual` | "Ist-Stunden" | `text-primary` (orange #ff6b35) |
| 2 | "Sollstunden" | `summary.total_target` | "Pro Monat" | `text-base-content` (default dark) |
| 3 | "Aktuelles Zeitkonto" | `summary.current_balance` | "Überstunden" | `text-success` if positive, `text-error` if negative |

### 4.4 Value Formatting

- Hours displayed as `HHH:MMh` format (e.g., "149:38h")
- Positive balance prefixed with `+` (e.g., "+19:30h")
- Negative balance prefixed with `-` (e.g., "-2:15h")

---

## 5. Time Entry Table Component

### 5.1 Table Container

```html
<div class="card bg-base-100 shadow-md border border-base-300 rounded-lg overflow-hidden">
    <div class="overflow-x-auto">
        <table class="table w-full">
            <!-- thead -->
            <!-- tbody -->
            <!-- tfoot -->
        </table>
    </div>
</div>
```

### 5.2 Table Header

**Background**: Dark slate (`bg-neutral` or custom `#3d4f5c`)
**Text**: White, bold, 14px

```html
<thead>
    <tr class="bg-neutral text-white">
        <th class="font-bold text-sm">Tag</th>
        <th class="font-bold text-sm">Ankunft</th>
        <th class="font-bold text-sm">Ende</th>
        <th class="font-bold text-sm">Pausen</th>
        <th class="font-bold text-sm">Arbeitsstunden Real</th>
        <th class="font-bold text-sm">Arbeitsstunden Soll</th>
        <th class="font-bold text-sm">+/-</th>
        <th class="font-bold text-sm">Abwesenheit / Bemerkung</th>
        <th class="font-bold text-sm text-center">Zeitausgleich</th>
        <th class="font-bold text-sm text-center">Urlaub?</th>
    </tr>
</thead>
```

### 5.3 Column Specifications

| Column | Header Text | Data Field | Width | Alignment | Special Styling |
|--------|-------------|------------|-------|-----------|-----------------|
| 1 | Tag | `entry.work_date` | ~100px | Left | Date format: DD.MM.YY |
| 2 | Ankunft | `entry.start_time` | ~100px | Left | Time format: HH:MM |
| 3 | Ende | `entry.end_time` | ~80px | Left | Time format: HH:MM |
| 4 | Pausen | `entry.break_duration` | ~95px | Left | Format: H:MMh |
| 5 | Arbeitsstunden Real | `entry.actual_hours` | ~200px | Left | Light blue bg (`bg-info/10`) **body cells only, NOT header** |
| 6 | Arbeitsstunden Soll | `entry.target_hours` | ~195px | Left | - |
| 7 | +/- | `entry.daily_balance` | ~85px | Left | Green if positive, red if negative |
| 8 | Abwesenheit / Bemerkung | `entry.notes` | ~250px | Left | Gray text color |
| 9 | Zeitausgleich | `entry.is_flex_time` | ~145px | Center | Checkbox |
| 10 | Urlaub? | `entry.is_vacation` | ~100px | Center | Checkbox |

### 5.4 Table Body Rows

**Zebra Striping**:
- Odd rows: `bg-base-100` (white)
- Even rows: `bg-base-200` (light gray `#f9fafb`)

**Row Structure**:
```html
<tr class="{{ 'bg-base-200' if loop.index is even else '' }} border-b border-base-300">
    <td class="py-3 px-4 text-sm">{{ entry.work_date.strftime('%d.%m.%y') }}</td>
    <td class="py-3 px-4 text-sm">{{ entry.start_time.strftime('%H:%M') if entry.start_time else '' }}</td>
    <td class="py-3 px-4 text-sm">{{ entry.end_time.strftime('%H:%M') if entry.end_time else '' }}</td>
    <td class="py-3 px-4 text-sm">{{ entry.break_duration|format_duration if entry.break_duration else '' }}</td>
    <td class="py-3 px-4 text-sm bg-info/10">{{ entry.actual_hours|format_hours if entry.actual_hours else '' }}</td>
    <td class="py-3 px-4 text-sm">{{ entry.target_hours|format_hours }}</td>
    <td class="py-3 px-4 text-sm {{ 'text-success' if entry.daily_balance >= 0 else 'text-error' }}">
        {{ entry.daily_balance|format_balance }}
    </td>
    <td class="py-3 px-4 text-sm text-base-content/70">{{ entry.notes or '' }}</td>
    <td class="py-3 px-4 text-center">
        <input type="checkbox" class="checkbox checkbox-sm"
               {{ 'checked' if entry.is_flex_time else '' }}
               hx-patch="/time-entries/{{ entry.id }}"
               hx-vals='{"is_flex_time": {{ "true" if not entry.is_flex_time else "false" }}}'
               hx-swap="none" />
    </td>
    <td class="py-3 px-4 text-center">
        <input type="checkbox" class="checkbox checkbox-sm"
               {{ 'checked' if entry.is_vacation else '' }}
               hx-patch="/time-entries/{{ entry.id }}"
               hx-vals='{"is_vacation": {{ "true" if not entry.is_vacation else "false" }}}'
               hx-swap="none" />
    </td>
</tr>
```

### 5.5 Conditional Row Styling

| Condition | Row Style | Notes Column Display |
|-----------|-----------|---------------------|
| Weekend day (no work) | All cells empty except date, +/-, notes | "Wochenende" |
| Holiday | All cells empty except date, target (if applicable) | Holiday name |
| Regular work day | All cells populated | User notes |
| Partial day entry | Some cells populated | Relevant notes |

### 5.6 Balance Column Color Logic

```jinja2
{% if entry.daily_balance > 0 %}
    text-success  {# Green: #00a63e #}
{% elif entry.daily_balance < 0 %}
    text-error    {# Red: #e7000b #}
{% else %}
    text-success  {# Zero displays as +0:00 in green #}
{% endif %}
```

---

## 6. "Add Next Day" Row

### 6.1 Structure

A special row at the end of the table body, before the footer:

```html
<tr class="bg-warning/10 border-b border-base-300">
    <td colspan="10" class="py-4">
        <button class="flex items-center justify-center gap-2 w-full text-primary font-medium"
                hx-get="/time-entries/new?date={{ next_date }}"
                hx-target="#modal-container"
                hx-swap="innerHTML">
            <!-- Plus icon (circle with +) -->
            <svg class="w-5 h-5" ...></svg>
            <span>Nächsten Tag hinzufügen ({{ next_date.strftime('%d.%m.%y') }})</span>
        </button>
    </td>
</tr>
```

### 6.2 Styling

- Background: Light orange tint (`bg-warning/10` or `#fff7ed`)
- Text color: Primary/orange (`text-primary` or `#ff6b35`)
- Font weight: Medium
- Icon: Plus circle icon in same orange color
- Row height: Slightly taller than data rows (~57px)

### 6.3 Behavior

- Clicking opens a modal/form to create a new time entry
- Pre-populated with the next calendar date after the last entry
- Example text: "Nächsten Tag hinzufügen (20.12.25)"

---

## 7. Table Footer (Summary Rows)

### 7.1 Container Styling

```html
<tfoot class="border-t-2 border-success bg-success/10">
    <!-- Row 1: Monthly totals -->
    <!-- Row 2: Current balance -->
</tfoot>
```

### 7.2 Row 1: Monthly Totals ("Monatssaldo")

```html
<tr class="bg-success/5">
    <td colspan="4" class="py-3 px-4 font-bold text-sm">Monatssaldo:</td>
    <td class="py-3 px-4 font-bold text-sm">{{ summary.total_actual|format_hours }}</td>
    <td class="py-3 px-4 font-bold text-sm">{{ summary.total_target|format_hours }}</td>
    <td colspan="4"></td>
</tr>
```

### 7.3 Row 2: Current Time Account ("Aktuelles Zeitkonto")

```html
<tr class="bg-success/20">
    <td colspan="4" class="py-3 px-4 font-bold text-sm">Aktuelles Zeitkonto:</td>
    <td class="py-3 px-4 font-bold text-sm text-success">{{ summary.current_balance|format_balance }}</td>
    <td colspan="5"></td>
</tr>
```

### 7.4 Footer Color Scheme

- Border top: 2px solid success green (`#b9f8cf`)
- Row 1 background: Very light green (`bg-success/5` or `#f0fdf4`)
- Row 2 background: Slightly darker green (`bg-success/20` or `#dcfce7`)
- Balance value: Bold green text (`text-success` or `#008236`)

---

## 8. Data Models

### 8.1 TimeEntry (for table rows)

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `work_date` | date | The calendar date |
| `start_time` | time | Work start time (nullable) |
| `end_time` | time | Work end time (nullable) |
| `break_duration` | timedelta | Total break time |
| `actual_hours` | timedelta | Calculated: end - start - break |
| `target_hours` | timedelta | Expected work hours for day |
| `daily_balance` | timedelta | actual - target |
| `notes` | str | Comments/remarks (nullable) |
| `is_flex_time` | bool | Zeitausgleich checkbox |
| `is_vacation` | bool | Urlaub checkbox |

### 8.2 MonthlySummary (for cards and footer)

| Field | Type | Description |
|-------|------|-------------|
| `month` | int | Month number (1-12) |
| `year` | int | Year |
| `total_actual` | timedelta | Sum of all actual hours |
| `total_target` | timedelta | Sum of all target hours |
| `period_balance` | timedelta | actual - target for month |
| `current_balance` | timedelta | Cumulative overtime balance |

---

## 9. Jinja2 Template Filters

### 9.1 Required Custom Filters

```python
@app.template_filter('format_hours')
def format_hours(td: timedelta) -> str:
    """Format timedelta as HHH:MMh (e.g., '149:38h')"""
    total_minutes = int(td.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}h"

@app.template_filter('format_duration')
def format_duration(td: timedelta) -> str:
    """Format timedelta as H:MMh (e.g., '0:30h')"""
    total_minutes = int(td.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}h"

@app.template_filter('format_balance')
def format_balance(td: timedelta) -> str:
    """Format timedelta with +/- prefix (e.g., '+1:16', '-0:45')"""
    total_minutes = int(td.total_seconds() // 60)
    prefix = '+' if total_minutes >= 0 else '-'
    abs_minutes = abs(total_minutes)
    hours = abs_minutes // 60
    minutes = abs_minutes % 60
    return f"{prefix}{hours}:{minutes:02d}"
```

---

## 10. HTMX Interactions

### 10.1 Month Navigation

```html
<button hx-get="/time-entries?month={{ prev_month }}&year={{ prev_year }}"
        hx-target="#time-entries-content"
        hx-swap="innerHTML"
        hx-push-url="true"
        class="btn btn-ghost btn-square">
```

### 10.2 Checkbox Toggle (Zeitausgleich/Urlaub)

```html
<input type="checkbox"
       class="checkbox checkbox-sm"
       hx-patch="/time-entries/{{ entry.id }}"
       hx-vals='{"field": "is_flex_time", "value": {{ not entry.is_flex_time | lower }}}'
       hx-swap="none"
       hx-trigger="change" />
```

### 10.3 Add New Entry

```html
<button hx-get="/time-entries/new?date={{ next_date.isoformat() }}"
        hx-target="#modal-container"
        hx-swap="innerHTML">
```

### 10.4 Row Click (Optional Detail View)

```html
<tr hx-get="/time-entries/{{ entry.id }}"
    hx-target="#detail-pane"
    hx-swap="innerHTML"
    class="cursor-pointer hover:bg-base-200">
```

---

## 11. Template File Structure

### 11.1 New Templates to Create

| File | Purpose |
|------|---------|
| `templates/pages/zeiterfassung.html` | Main page container |
| `templates/partials/_monthly_view.html` | Complete monthly view partial |
| `templates/partials/_month_navigation.html` | Month nav component |
| `templates/partials/_summary_cards.html` | Three summary cards |
| `templates/partials/_time_entry_table.html` | Main data table |
| `templates/partials/_time_entry_row.html` | Single table row partial |
| `templates/partials/_table_footer.html` | Summary footer rows |

### 11.2 Template Hierarchy

```
zeiterfassung.html (extends base.html)
└── _monthly_view.html
    ├── _month_navigation.html
    ├── _summary_cards.html
    └── _time_entry_table.html
        ├── _time_entry_row.html (loop)
        └── _table_footer.html
```

---

## 12. Color Reference

### 12.1 Color Palette from Design

| Color | Hex | Usage | Tailwind/daisyUI Class |
|-------|-----|-------|------------------------|
| Primary Orange | `#ff6b35` | Monatssaldo value, add button, icons | `text-primary` (configure in theme) |
| Success Green | `#00a63e` | Positive balance | `text-success` |
| Error Red | `#e7000b` | Negative balance | `text-error` |
| Dark Slate | `#3d4f5c` | Table header background | `bg-neutral` |
| Light Gray | `#f9fafb` | Alternating rows | `bg-base-200` |
| Border Gray | `#e5e7eb` | Table borders | `border-base-300` |
| Text Gray | `#4a5565` | Notes/remarks text | `text-base-content/70` |
| Light Blue | `#eff6ff` | Arbeitsstunden Real column | `bg-info/10` |
| Light Orange | `#fff7ed` | Add row background | `bg-warning/10` |
| Footer Green 1 | `#f0fdf4` | First footer row | `bg-success/5` |
| Footer Green 2 | `#dcfce7` | Second footer row | `bg-success/20` |
| Footer Border | `#b9f8cf` | Footer top border | `border-success` |

### 12.2 daisyUI Theme Configuration (if needed)

```javascript
// tailwind.config.js
module.exports = {
  daisyui: {
    themes: [{
      verk: {
        "primary": "#ff6b35",
        "success": "#00a63e",
        "error": "#e7000b",
        "neutral": "#3d4f5c",
        // ... other theme colors
      }
    }]
  }
}
```

---

## 13. Responsive Behavior

### 13.1 Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| Mobile (<768px) | Summary cards stack vertically, table scrolls horizontally |
| Tablet (768px-1024px) | 2 cards per row, table scrolls horizontally |
| Desktop (>1024px) | 3 cards per row, full table visible |

### 13.2 Table Overflow

The table container should have `overflow-x-auto` to enable horizontal scrolling on smaller screens:

```html
<div class="overflow-x-auto">
    <table class="table w-full min-w-[1200px]">
        ...
    </table>
</div>
```

---

## 14. Accessibility Considerations

### 14.1 Semantic HTML

- Use proper `<table>`, `<thead>`, `<tbody>`, `<tfoot>` structure
- Include `scope="col"` on header cells
- Use `aria-label` on navigation buttons

### 14.2 Keyboard Navigation

- All interactive elements must be focusable
- Checkboxes accessible via Tab key
- Navigation buttons keyboard accessible

### 14.3 Screen Reader Support

```html
<button aria-label="Vorheriger Monat">
    <!-- chevron-left icon -->
</button>
<button aria-label="Nächster Monat">
    <!-- chevron-right icon -->
</button>
```

---

## 15. API Endpoints

### 15.1 Required Endpoints

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| GET | `/time-entries` | List entries for current/specified month | `_monthly_view.html` partial |
| GET | `/time-entries?month=X&year=Y` | List entries for specific month | `_monthly_view.html` partial |
| GET | `/time-entries/new?date=YYYY-MM-DD` | New entry form | `_new_time_entry.html` |
| POST | `/time-entries` | Create new entry | `_time_entry_row.html` + HX-Trigger |
| PATCH | `/time-entries/{id}` | Update entry (checkbox toggle) | 204 No Content or updated row |

### 15.2 Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `month` | int (1-12) | Month to display |
| `year` | int | Year to display |
| `employee_id` | int (optional) | Filter by employee |

---

## 16. Notes for Implementation

### 16.1 Data Considerations

- Sample data in the Figma is for demonstration only
- The `target_hours` (Sollstunden) of 6:24h per day appears to be a specific contract configuration
- Weekend days show in the list but with empty time fields and "Wochenende" note
- The "Zeitausgleich: None" in the notes column appears to be a debug/placeholder value - implement as user-editable notes

### 16.2 Business Logic Notes

- "Arbeitsstunden Real" (actual hours) = end_time - start_time - break_duration
- Daily balance = actual_hours - target_hours
- Current time account balance = sum of all daily balances (cumulative overtime)
- Monatssaldo = sum of actual hours for the displayed month

### 16.3 Checkbox Behavior

The "Zeitausgleich" and "Urlaub?" checkboxes:
- Toggle via HTMX PATCH request
- Update the database immediately (no form submission required)
- May affect balance calculations depending on business rules

---

## 17. Implementation Checklist

- [ ] Create page template `zeiterfassung.html`
- [ ] Create month navigation partial
- [ ] Create summary cards partial
- [ ] Create time entry table partial
- [ ] Create table row partial
- [ ] Create table footer partial
- [ ] Implement custom Jinja2 filters for time formatting
- [ ] Configure daisyUI theme colors
- [ ] Implement HTMX endpoints
- [ ] Add responsive breakpoint handling
- [ ] Test keyboard accessibility
- [ ] Verify zebra striping
- [ ] Test checkbox toggle functionality
- [ ] Verify color contrast for accessibility
