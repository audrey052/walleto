# Tasks

## 0. Before starting

- [x] 0.1 Confirm `add-dashboard` is archived, so that `openspec/specs/dashboard/spec.md` exists; verify with `openspec list --specs`. If it is not archived, stop and ask the developer.

## 1. Period

- [x] 1.1 `finance/periods.py`:
  - `Period(start, end)` with `is_month`, `days`, `month`, `previous()`, `query()`, `label`, `prev_month()` and `next_month(today)`;
  - `parse_period(params, today)`.

  Verify unit tests for:
  - "Old month link", "Range link", "A range that is a whole month";
  - "Future end date", "Reversed range", "Too long", "Unreadable dates";
  - `from`/`to` winning over `month`;
  - every label form;
  - the previous period (month and 15 days);
  - "Previous from a range" and "Next from a range in an earlier month".
- [x] 1.2 `in_period(start, end)` on the Transaction, Transfer and GoalContribution querysets, with `in_month` delegating to it; verify tests that both end days are included and that the existing month tests still pass

## 2. Transactions

- [x] 2.1 `_activity`, `transaction_list`, `transaction_export` and `transactions_url` take a `Period`:
  - pagination, filter and clear links keep the period;
  - the CSV file name follows the spec.

  Verify tests for "A range of days", "Range summary", "Filters keep the range", "Export a range", and that a whole month still exports `walleto-transactions-2026-11.csv`.
- [x] 2.2 Privacy for ranges; verify a test that another user's entries inside the range appear neither in the list, the summary nor the export

## 3. Home

- [x] 3.1 `period_summary(user, period, today)`:
  - previous-period totals;
  - plan, projection and budget line only for a whole month;
  - range categories with `share`;
  - `compare_label`.

  Verify tests for "Change against the previous days", "Range bars", "Share in a range" and "A range is not a month", plus `assertNumQueries` (5 for a month, 3 for a range).
- [x] 3.2 Update `views_dashboard.py` and `dashboard.html`:
  - the range note in place of Remaining, with "Show <Month YYYY>";
  - the comparison label;
  - the share column and footnote;
  - the chart footer label;
  - `axis_labels` for more than 31 bars;
  - category links that carry the period.

  Verify page tests for these, and "Same numbers for a range" against the Transactions page.
- [x] 3.3 Privacy for ranges; verify a test that another user's expenses in the range don't reach the totals, the chart or Where it goes

## 4. Picker

- [x] 4.1 `templates/components/period_picker.html`:
  - arrows, label, and a `<details>` popover with the calendar and the From/To/Apply form;
  - hidden filter fields on Transactions;
  - HTMX swap of `#dashboard` or `#results` with push URL.

  Use it on Home and Transactions. Verify template tests that both pages render the form, and that the next arrow is absent in the current month.
- [x] 4.2 Alpine `periodPicker` in `static/js/app.js` and styles in `static/src/app.css`:
  - month grid with month steps up to the current month, start and end clicks, range highlight, days after today disabled;
  - closes on Escape or an outside click;
  - submits the form on the end click;
  - then `npm run css:build`.

  Verify in Edge (demo account) for "Pick a range" and "Future days" on both pages: the content swaps with no full navigation and the address updates.
- [x] 4.3 No-JavaScript and narrow-width checks; verify in Edge with JavaScript off that Apply loads 10 to 24 November on both pages, and that at 520px the popover fits on screen with no horizontal page scroll

## 5. Wrap-up

- [x] 5.1 Update `docs/STYLE.md` (picker and page rows) and `docs/decisions.md` (period type, `?month=` kept, no prorated plan, no date library); verify that `python manage.py test` and `openspec validate add-date-range --strict` pass
- [x] 5.2 Write `changes.md` and the commit record in `openspec/commits/`; verify the index lists it

## Workflow follow-up

- The developer tries a few ranges on Home and Transactions in a real browser, then archives with `/opsx:archive add-date-range`.
