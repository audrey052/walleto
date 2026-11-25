# Design: add-date-range

## Context

See proposal.md for why.

- **Month only today.** Both pages read `?month=` with `finance/months.py::parse_month` and query with `in_month(year, month)` on the Transaction, Transfer and GoalContribution querysets.
- **Transactions.** `finance/views_activity.py::_activity` builds every query once for the page and the CSV export. `transactions_url(year, month, **filters)` builds every link. The filter form keeps the month in a hidden `month` field.
- **Home.** `finance/summary.py::month_summary` returns a frozen `MonthSummary` in a fixed 5 queries: two-month totals, `month_budget` (3), daily totals.
- **Month picker markup.** Copied in `dashboard.html`, `transactions.html` and `budget.html`. Home switches months with HTMX `hx-select="#dashboard"`; Transactions uses plain links.
- **Existing front-end pieces.** Alpine components live in `static/js/app.js`, and `.popover` exists in `app.css`. There is no date-picker library.
- **Dependency.** `add-dashboard` is not archived yet, so `openspec/specs/dashboard/spec.md` does not exist. This change's dashboard delta modifies requirements that `add-dashboard` adds, so `add-dashboard` must be archived first.

## Goals / Non-Goals

**Goals:**
- One period type shared by both pages, so every link, query and label agrees.
- The plan and budget figures keep their monthly meaning and are never prorated.
- A fixed number of queries on both pages, whatever the range.

**Non-Goals:**
- Changing Budget, the after-save redirect (which still opens the saved entry's month), or Wallets links.
- Any new model, field or migration.

## Decisions

### 1. A `Period` value in `finance/periods.py`

A frozen dataclass `Period(start, end)`, both dates inclusive, with:

| Member | Meaning |
|---|---|
| `is_month` | `start` is day 1, `end` is the month's last day, and both are in the same month |
| `days` | `(end - start).days + 1` |
| `month` | `(year, month)` when `is_month` |
| `previous()` | a whole month: the month before; otherwise: the same number of days ending the day before `start` |
| `query()` | `{"month": "YYYY-MM"}` or `{"from": …, "to": …}` |
| `label` | "November 2026", "10 Nov – 24 Nov 2026", "28 Dec 2025 – 3 Jan 2026", "24 Nov 2026" |
| `prev_month()`, `next_month(today)` | the arrow targets (decision 5); next is `None` once that month starts after today |

- `parse_period(params, today)` reads the `from` and `to` pair first, then `month`, then falls back to the current month.
- It applies the spec rules in order: clamp `end` to today, swap a reversed pair, cut ranges to 92 days, and treat a whole-month range as that month.
- `months.py` stays for Budget. `parse_period` reuses `parse_month` for `?month=`.

*Rejected: separate `start`/`end` arguments threaded through every function.* The whole-month rules (address, label, plan) would be duplicated in each view.

### 2. Address format: keep `?month=` for whole months

- A whole month always serialises as `?month=YYYY-MM`, even when picked as 1–30 in the calendar. This keeps today's links, the Budget and after-save links, and the existing tests valid.
- Custom ranges use `from` and `to` in ISO format.

*Rejected: always `from`/`to`.* It would break every existing `?month=` link, and the address would not show that a month is selected.

### 3. Queries: `in_period(start, end)`

- Add `in_period` beside `in_month` on the three querysets: `date__gte=start, date__lte=end`.
- `in_month` stays as a thin wrapper for Budget and the other callers.
- In `_activity`, `in_month(year, month)` becomes `in_period(period.start, period.end)`, and the context carries `period` instead of `year` and `month`.
- `transactions_url(period, **filters)` merges `period.query()` with the filters.
- The hidden `month` field becomes hidden fields from `period.query()`, so filters keep the range.

### 4. Home: `period_summary(user, period, today)`

- `month_summary` becomes `period_summary`, and its value type `PeriodSummary` gains `period`, `is_month` and `compare_label`.
- **Totals:** one aggregate with two conditional sums over `period.previous().start .. period.end`, the same shape as today.
- **Plan:** `month_budget` (3 queries) runs only when `period.is_month`. Otherwise `plan`, `remaining`, `projection`, `daily_budget` and the budget percents are `None` and `has_plan` is `False`, so the query count drops to 2 for ranges.
- **Categories:**
  - a whole month keeps `category_lines(month_plan)`;
  - a range uses one `values("category").annotate(Sum)` query, and each line's `share` is `spent * 100 // total`;
  - `CategoryLine` gains `share`, and `percent` stays `None` for ranges.
  - Ranges are therefore 3 queries, and a test pins 5 for a month and 3 for a range.
- **Chart:** `_daily_expenses` and `daily_chart` take `period`, with one bar per day from `start` to `end`, `is_future` for days after today and no budget line without a plan.
- **Comparison label:** "vs. last month", "vs. previous day", or "vs. previous N days".

*Rejected: prorating the monthly plan to the range* (e.g. plan × 15/30). That number appears on no other page and would contradict the Budget page.

### 5. Arrows

- From a whole month the arrows move to `shift(month, ±1)`.
- From a range, previous opens the month before `start`'s month, and next opens the month after `end`'s month.
- Both are `?month=` links. Next is hidden when that month starts after today.

### 6. The picker: `components/period_picker.html` and Alpine `periodPicker`

- **One include** for both pages takes `period`, `prev_url`, `next_url`, `base_url`, a `target` (`#dashboard` or `#results`) and the hidden filter params to keep.
- **Markup:** `‹ [calendar label] ›`. The middle button toggles a `.popover` that holds:
  1. a `<form method="get">` with `from` and `to` `<input type="date" max=today>` fields and "Apply". This is the no-JavaScript path, and on Transactions the form also carries the filter params;
  2. `<div x-show="ready">`, the calendar the component draws.
- **Without JavaScript,** the popover is a `<details>`/`<summary>`, so it opens and closes natively.
- **With Alpine,** `periodPicker`:
  - closes the popover on Escape or an outside click;
  - draws a month grid (Monday first, matching `j M` dates) with ‹ › month steps, capped at the current month;
  - takes the first click as the start and the second as the end, swapping if earlier, and highlights the days between on hover;
  - disables days after today;
  - on the end click, fills the two date inputs and calls `htmx.trigger(form, "submit")`, so the server applies every rule in decision 1;
  - hides the date fields once it is ready.
- **The calendar is drawn in JavaScript;** the server only renders the form and links. HTMX swaps `#dashboard` or `#results` with `hx-push-url`, as Home does now.
- **Transactions changes too:** its arrows gain the same HTMX swap so both pages behave alike.

*Rejected: a date-picker library (flatpickr, Litepicker).* It adds a vendored file and its own styles to restyle to STYLE.md tokens. The grid is about 120 lines of Alpine.

*Rejected: native date inputs only.* The developer chose a calendar. Quick picks (This month, Last month, Last 7 days, Last 30 days) were built first and removed at the developer's request: the arrows already give whole months.

### 7. Home page copy and layout for ranges

- The Remaining block shows "The monthly plan shows when a whole month is selected." with a "Show <Month YYYY>" link to the month of `end`, centred like the no-plan state.
- In Where it goes, a range row's right column shows "60%" from `share` in `text-secondary`. The footnote becomes "Share of spending in this period".
- The chart footer shows the period label instead of "01–DD Mon YYYY".
- `axis_labels` works on any list of bars:
  - ≤ 31 bars: today's rules (days 1, 5, 10, 15, 20, 25, the last day and today);
  - more than 31 bars: the first day of each month as "1 Dec", plus the last day and today.
  - The ±1-day gap rule stays.

## Risks / Trade-offs

- **[92 bars are thin at 520px]** → the bars keep their `min-w-0 flex-1` and 2px gap, and the tooltip carries the exact figure. The 92-day cap bounds it.
- **[The calendar needs JavaScript]** → the date fields in the same popover work without it, and the server validates either way.
- **[`?month=` and `from`/`to` both present]** → `from`/`to` wins. A test covers it.
- **[Day boundaries]** → every date is `timezone.localdate()` (Asia/Jakarta), as today.
- **[The dashboard delta depends on `add-dashboard` being archived]** → archive `add-dashboard` before applying this change. Task 0 checks it.

## Migration Plan

- No data migration. Old `?month=` links keep working.
- Rollback is a revert of the change's commits.

## Open Questions

- None.
