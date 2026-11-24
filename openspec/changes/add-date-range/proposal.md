# Proposal: add-date-range

## Why

Home and Transactions show one calendar month at a time. The developer wants to look at any stretch of days, such as 10 to 24 November, without leaving the month-by-month flow.

## What Changes

- **Date range picker on Home and Transactions.** The calendar button in the month picker opens a popover with:
  - a calendar where the user clicks a start date and an end date (no quick picks: the developer removed them after the first build);
  - without JavaScript, two date fields and an "Apply" button.
- **The ‹ › arrows still move by whole calendar month.** From a custom range, ‹ opens the month before the range's start and › opens the month after its end, if that month has started.
- **The address carries the period:**
  - a whole calendar month keeps `?month=YYYY-MM`, so existing links keep working;
  - any other range uses `?from=YYYY-MM-DD&to=YYYY-MM-DD`.
- **Period rules:**
  - no dates after today;
  - a reversed range is swapped;
  - a range longer than 92 days is cut to 92 days from its start;
  - invalid values fall back to the current month.
- **Picker label:**
  - a whole month reads "November 2026";
  - other ranges read "10 Nov – 24 Nov 2026", or "28 Dec 2025 – 3 Jan 2026" across years.
- **Transactions follows the range.** The list, the summary line, the filters, pagination and Export CSV all use the period. A range export is named `walleto-transactions-2026-11-10_2026-11-24.csv`. A whole month keeps `walleto-transactions-2026-11.csv`.
- **Home follows the range:**
  - Total income and Total expenses are compared with the previous period of the same length: "vs. last month" for a whole month, "vs. previous 15 days" otherwise.
  - The daily chart has one bar per day of the range.
  - Where it goes lists the range's categories.
  - Category rows open Transactions for the same range.
- **The monthly plan stays monthly.** "Remaining this month", the meal-days line, the daily budget line and the percent of each category's budget show only when the range is exactly one calendar month. For other ranges:
  - the Remaining block is replaced by a short note with a link to the whole month;
  - Where it goes shows each category's share of the range's spending.
- Switching periods swaps the content with HTMX and pushes the address, as the month picker does today.

### Out of scope

- Budget keeps its month-only picker, because plans and category limits are per month.
- Ranges longer than 92 days, yearly views, and weekly or monthly grouping in the chart.
- Saving a preferred range between visits.
- Comparing two arbitrary ranges side by side.

## Capabilities

### New Capabilities

- `period-picker`: the shared month and date range control: popover, arrows, label, address format, and the rules for valid periods.

### Modified Capabilities

- `transactions`: "One month at a time", "Month summary line", "Filter and search", "Pagination" and "Export to CSV" now refer to the selected period instead of the month.
- `dashboard`: "Dashboard month", "Remaining this month", "Income and expenses", "Daily spending chart", "Where it goes" and "Figures match the other pages" now cover a period; the plan figures only appear for a whole month.
  - **Depends on `add-dashboard` being archived first**, so that `openspec/specs/dashboard/spec.md` exists for these deltas.

## Impact

- New `finance/periods.py`: the `Period` value, address parsing, labels and the previous period.
- New `templates/components/period_picker.html` and an Alpine `periodPicker` component in `static/js/app.js` (calendar grid, start and end clicks), plus styles in `static/src/app.css`.
- `finance/models.py`: an `in_period(start, end)` queryset method beside `in_month` for transactions, transfers and goal contributions.
- `finance/views_activity.py`:
  - `_activity`, `transaction_list` and `transaction_export` use a period;
  - `transactions_url` takes a period.
- `finance/summary.py`: `month_summary` becomes `period_summary`, with the monthly plan only for whole months.
- `finance/views_dashboard.py` and `templates/finance/dashboard.html`: the period, the comparison label, the note instead of Remaining, and the share column in Where it goes.
- `templates/finance/transactions.html`: the shared picker.
- Tests for periods, both pages, the export name and privacy.
- No model or migration changes. No new dependencies.
