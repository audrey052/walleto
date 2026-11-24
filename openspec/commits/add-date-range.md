# Pick a Date Range on Home and Transactions

**Created:** 2026-11-25
**Last edited:** 2026-11-25
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `8a7b492`
**OpenSpec change:** `add-date-range`, tasks 0.1–5.2
**Trigger:** The developer asked for the calendar button to select a date range; they chose Home and Transactions (Budget stays monthly) and a calendar with quick picks. Then `/opsx:apply add-date-range`. After the first build they asked to drop the quick picks and keep only dates.

## Why this is recorded here

Both pages stop being month-only. A new `Period` type decides every address, query and label, and the Home summary learns to leave the monthly plan out of ranges.

## Context

- A whole month keeps `?month=YYYY-MM`. Other ranges use `?from=&to=`, at most 92 days and never past today.
- The monthly plan is never prorated. Remaining, the meal-days line, the daily budget line and the budget percents appear only for a whole month.

## What is built

| Area | Change |
|---|---|
| `finance/periods.py` | `Period`, `parse_period()` |
| Querysets | `in_period(start, end)` for transactions, transfers and goal movements |
| Transactions | list, summary, filters, pages and Export CSV follow the period; `walleto-transactions-2026-11-10_2026-11-24.csv` for a range |
| Home | `period_summary()`: previous period of the same length ("vs. previous 15 days"), one bar per day, Where it goes as share of the period's spending, a note with "Show November 2026" instead of Remaining |
| Picker | `components/period_picker.html` + Alpine `periodPicker`: arrows by whole month, popover with a calendar (start day, end day); From/To/Apply without JavaScript |

## Requirements this establishes

1. **Every period on Home and Transactions comes from `parse_period()`.** No view reads `?month=` itself any more.
2. **The plan figures belong to whole months only.**
3. **Home's summary query count is fixed:** 5 for a month, 3 for a range. A test pins both.

## Files changed

| File | Change |
|---|---|
| `finance/periods.py`, `templates/components/period_picker.html` | new |
| `finance/models.py`, `views_activity.py`, `summary.py`, `views_dashboard.py` | periods |
| `templates/finance/dashboard.html`, `transactions.html` | the picker and range copy |
| `static/js/app.js`, `static/src/app.css` | `periodPicker`, `.period-*` |
| `finance/tests/test_periods.py` (new), `test_activity.py`, `test_summary.py`, `test_dashboard.py` | 43 new tests |
| `openspec/changes/add-date-range/` | proposal, specs, design, tasks (all ticked), changes |
| `openspec/commits/README.md`, `archive-add-dashboard.md` | `8a7b492` filled in, this record |

## Verification

**Executed:**

- `python manage.py test`: 397 tests OK.
- `openspec validate add-date-range --strict`: valid.
- Edge headless, demo account, on Home and Transactions:
  - calendar pick 10–24 Nov and the previous arrow each swap the page with no full navigation and update the address;
  - days after today are disabled;
  - with JavaScript off, Apply loads the range;
  - at 520px the popover fits and the page does not scroll sideways.

**Not executed:**

- The developer's own browser pass.

## Known gaps

- **Ranges are capped at 92 days.** Longer views (a year) would need weekly bars; out of scope.
