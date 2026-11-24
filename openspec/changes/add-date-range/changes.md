# Changes: add-date-range

This is the implementation log for this change. It lists what was created or modified, and where the result differs from `proposal.md`, `design.md` and `tasks.md`. Per-commit detail is in `openspec/commits/`.

- **Status:** implemented, not archived. Still open: the developer's real-browser check.
- **Date:** 2026-11-25
- **Tests:** 397 passing (43 new):
  - `finance/tests/test_periods.py` (19);
  - range classes in `test_activity.py` (7), `test_summary.py` (7) and `test_dashboard.py` (10).
- **Validation:** `openspec validate add-date-range --strict` passes.
- **Migrations:** none; `makemigrations --check` would find nothing, as no model fields changed.

## Commits

| Commit | Message | Record |
|---|---|---|
| this commit | feat: pick a date range on home and transactions | `add-date-range.md` |

## Routes

No new routes. `/` (`core:dashboard`), `/transactions/` and `/transactions/export/` now also read `?from=YYYY-MM-DD&to=YYYY-MM-DD`. `?month=YYYY-MM` keeps working.

## Files

| File | Change |
|---|---|
| `finance/periods.py` | new: `Period` (`is_month`, `days`, `previous()`, `query()`, `label`, `slug`, `prev_month()`, `next_month()`), `parse_period()` |
| `finance/models.py` | `in_period(start, end)` on the Transaction, Transfer and GoalContribution querysets; `in_month` calls it |
| `finance/views_activity.py` | `_activity`, the page and the export use a `Period`; `transactions_url(period, **filters)`; picker context; export name from `period.slug` |
| `finance/summary.py` | `period_summary()` and `PeriodSummary` (with `compare_label`); range categories with `share`; plan only for a whole month; `month_summary()` kept as a wrapper |
| `finance/views_dashboard.py` | the period, the "Show <Month>" link, `chart_footer`; `axis_labels` for any run of days |
| `templates/components/period_picker.html` | new: arrows, `<details>` popover with the calendar and the From/To form |
| `templates/finance/dashboard.html` | the picker; range note in place of Remaining; comparison label; share column and footnote |
| `templates/finance/transactions.html` | the picker; the page wrapped in `#transactions-page`; filter form keeps the period; labels use `period.label` |
| `static/js/app.js` | Alpine `periodPicker` |
| `static/src/app.css` | `.period-*` styles |
| `finance/tests/…` | see Tests |

## Differences from the plan

- **Transactions swaps `#transactions-page`, not `#results`.** Design decision 6 named `#results`, but the picker sits in the page heading, outside `#results`, so its label would not have updated. The whole page content is now wrapped and swapped. Filters still swap `#results` only.
- **Transactions context:** `month_param`, `month_start` and `is_current_month` are gone. Templates and tests read `period`.
- **Axis labels in a range:** a label next to one already shown is left out, as in a month. A week starting on the 9th shows "09" and "15" but not "10". A range across two months names the month on its first day and on the 1st ("26 Oct", "1 Nov").
- **Calendar highlight stops at today** in the current month, though the period runs to the month's last day.
- **On Transactions the date button and "Add transaction" share one width** (equal grid columns, both grow with a long label), at the developer's request. Both are as narrow as the date label allows (200px for "November 2026"); below 640px they stack at that same width.
- **No quick picks.** "This month", "Last month", "Last 7 days" and "Last 30 days" were built, then removed at the developer's request; the popover is only the calendar (300px wide).

## Verification

- `python manage.py test`: 397 tests OK.
- Edge headless, demo account, 1440px, on Home and Transactions:
  - the popover opens with the calendar, the date fields are hidden, 25 Nov and later are disabled, and there is no later month;
  - choosing 10 then 24 November gives `?from=2026-11-10&to=2026-11-24` and the label "10 Nov – 24 Nov 2026", with 0 full navigations;
  - the previous arrow gives `?month=2026-10`; no page errors;
  - after removing the quick picks, the popover shows only the calendar (1066–1366px at 1440px).
- Edge with JavaScript off: opening the `<details>`, entering 10 and 24 November and choosing Apply loads `/?from=2026-11-10&to=2026-11-24` and `/transactions/?from=2026-11-10&to=2026-11-24`.
- 520px: the popover spans 16–316px of 518px, and the page does not scroll sideways.

## Open before archiving

- The developer tries a few ranges on Home and Transactions in a real browser, then runs `/opsx:archive add-date-range` (the `dashboard`, `transactions` deltas are MODIFIED and `period-picker` is new).
- `docs/STYLE.md` and `docs/decisions.md` are updated locally only (`.gitignore`).
