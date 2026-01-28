# Feature Idea Tracker

**Last Updated**: 2026-01-28
**Status**: Active

---

## Ranking Guide

Use priority levels:

- **P1** - High priority, implement soon
- **P2** - Medium priority, good to have
- **P3** - Low priority, nice to have
- **SKIP** - Not pursuing

---

## Ideas (Unranked)

| ID  | Idea                                           | Category     | Complexity | Priority                           |
| --- | ---------------------------------------------- | ------------ | ---------- | ---------------------------------- |
| 01  | Working Now timer (start/stop tracking)        | Core Feature | Medium     | SKIP                               |
| 02  | Auto-suggest break time for >6h work           | UX           | Low        | P2                                 |
| 03  | Weekend detection warning                      | Validation   | Low        | SKIP(\*1)                          |
| 04  | Trend visualization (balance sparkline)        | Analytics    | Medium     | P2                                 |
| 05  | Annual overview (vacation/sick/overtime stats) | Analytics    | High       | P3                                 |
| 06  | Submit week action (lock entries)              | Workflow     | Medium     | SKIP(\*2)                          |
| 07  | Undo last action with toast                    | UX           | Medium     | P3                                 |
| 08  | Draft indicator on months                      | UI           | Low        | P2(See \*2)                        |
| 09  | Monthly PDF export                             | Export       | Medium     | P1: (In the works in another chat) |
| 10  | CSV export                                     | Export       | Low        | P1: (In the works in another chat) |
| 11  | Dark mode toggle                               | UI           | Medium     | SKIP                               |
| 12  | Notes quick-preview on hover                   | UX           | Low        | What is notes?                     |
| 13  | Mobile swipe actions                           | Mobile       | High       | SKIP(\*3)                          |
| 14  | Larger mobile touch targets                    | Mobile       | Low        | SKIP(\*3)                          |

**Notes**:
*1: Make entries of weekend visually distinct (different row color), and pick another (more warning) color for rows on days that are marked as no workdays in settings
*2: Until this tool exits the internal use stage, "submit" will be "soft" (no-lock) and just shows what was already exported (and printed for manual submission)
\*3: Mobile support is FAR off

---

## In Progress

| ID  | Idea | Assigned To | Status |
| --- | ---- | ----------- | ------ |

---

## Completed

| ID  | Idea                               | Completed Date | Notes                                                      |
| --- | ---------------------------------- | -------------- | ---------------------------------------------------------- |
| 15  | Consistent Lucide icons across app | 2026-01-28     | Replaced umbrella→tree-palm, verified all SVGs from Lucide |
| 18  | Auto-sort table by date            | 2026-01-28     | Changed to ascending (chronological) order                 |
| 16  | Logo branding: Zeiterfassung text  | 2026-01-28     | Added "Zeiterfassung" next to logo in header               |
| 17  | Historical balance card for past months | 2026-01-28 | Shows "Endsaldo [Monat]" for past months                   |
| 02  | Auto-suggest break time for >6h work    | 2026-01-28 | JS auto-fills 30min break when duration >6h                |
| 04  | Balance trend sparkline                 | 2026-01-28 | SVG sparkline showing 8-week balance trend                 |
| 20  | Auto-refresh on edits                   | 2026-01-28 | Summary cards refresh when entries change                  |

---

## Ideas (Sorted from User Additions)

| ID  | Idea                                       | Category  | Complexity | Priority | Notes                                               |
| --- | ------------------------------------------ | --------- | ---------- | -------- | --------------------------------------------------- |
| 16  | Logo branding: "[Verk logo] Zeiterfassung" | UI        | Low        | P2       | Match verk-bookkeeping style                        |
| 17  | Historical balance card for past months    | Analytics | Medium     | P2       | Show end-of-month balance instead of current        |
| 19  | Preset autofill for new rows               | UX        | Low        | WORKS    | Already implemented, user tested on holiday by mistake |
| 20  | Update table content on edits / refresh    | UX        | Medium     | P2       | State refresh after edits                           |
| 21  | Import VaWW modal components               | UI        | Low        | P2       | Replace browser confirms with styled modals         |

**#21 Details:**
- Source: `/home/tomge/work/clients/vaw/verk-bookkeeping/templates/components/_modal_confirm_delete.html`
- Source: `/home/tomge/work/clients/vaw/verk-bookkeeping/templates/components/_modal_confirm_discard.html`
- Replace `hx-confirm` browser dialogs with styled daisyUI modals
- Provides consistent UX with VaWW main app

---

## Bugs

| ID  | Bug                                            | Category | Priority | Status | Notes                                   |
| --- | ---------------------------------------------- | -------- | -------- | ------ | --------------------------------------- |
| B1  | Holiday badge only appears after absence click | UI       | P1       | FIXED  | Missing variable extraction in template |
