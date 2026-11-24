# Changes: add-dashboard (MVP 5)

This is the implementation log for this change. It lists what was created or modified, and where the result differs from `proposal.md`, `design.md` and `tasks.md`. Per-commit detail is in `openspec/commits/`.

- **Status:** implemented, not archived. Still open: the developer's real-browser check.
- **Date:** 2026-11-24
- **Tests:** 352 passing in about 11 s; 43 new in `finance/tests/test_summary.py` and `finance/tests/test_dashboard.py`.
- **Validation:**
  - `openspec validate add-dashboard --strict` passes.
  - `makemigrations --check` finds no changes (no model changes).

## Commits

| Commit | Message | Record |
|---|---|---|
| this commit | feat: add the dashboard | `add-dashboard.md` |

## Routes

| Method | URL | Name | Purpose |
|---|---|---|---|
| GET | `/` (`?month=YYYY-MM`) | `core:dashboard` | the Dashboard for the month; now `finance.views_dashboard.dashboard` |

The placeholder `core.views.dashboard` is removed. The route keeps its name and address, so the sign-in redirect and the sidebar are unchanged.

## Files

| File | Change |
|---|---|
| `finance/summary.py` | new: `month_summary()` and `MonthSummary`; pure helpers `change_tenths`, `projection`, `nice_top`, `short_amount`, `daily_chart`, `category_lines` |
| `finance/views_dashboard.py` | new: the page view, the change label ("10.3%" with direction) and the x-axis labels |
| `core/urls.py`, `core/views.py` | `core:dashboard` points at the new view; placeholder view deleted |
| `templates/finance/dashboard.html` | new: heading with month picker, balance overview, daily chart, Where it goes |
| `static/src/app.css` | daily chart components: dashed budget line, bars, CSS tooltip |
| `finance/tests/test_summary.py` | new: change, projection, chart helpers, month summary, figures match, query count |
| `finance/tests/test_dashboard.py` | new: page, month picker, privacy, axis labels |

## Differences from the plan

- **Scope cut before implementation, at the developer's request:** no wallet filter, no insight row, no Recent transactions. The artifacts were updated before `/opsx:apply`.
- **Chart top value is rounded to a "nice" step** (1, 2, 2.5 or 5 × 10ⁿ, times four), so the five y-axis labels are round ("0, 200k, 400k, 600k, 800k"). The design only said "max of the bars and the daily budget".
- **The day right next to today loses its x-axis label** (for example 25 when today is 24); at 520px wide the two ran together as "2425".
- **The chart panel stretches to the height of Where it goes,** so the two panels line up as in Figma.
- **No trend lines on Total income and Total expenses,** at the developer's request after implementation: the cards show the total and the change only, the summary reads two months instead of six, and `{% sparkline %}` stays deleted.
- **No "Remaining this month" label when the month has no plan,** at the developer's request: the block starts with "<Month> has no monthly plan".
- **Centred empty states:** the no-plan block and the empty "Where it goes" are centred in their panels.
- **No info icon next to "Remaining this month",** removed by the developer.
- **An empty month's chart runs 0–100k,** so the y-axis never reads "0k" four times.
- **The Remaining line counts days of meals,** at the developer's request: the remainder ÷ Rp50.000 a day ("Enough for 37 days of meals at Rp50.000 a day"), replacing "Enough until <date> at your current pace". The line sits evenly between the amount and the progress bar.
- **No-limit categories** get a bar relative to the largest category, in the category colour, and "No limit" in place of the percent.
- **The "Add transaction" button from the Figma heading is not on the page.** It was not in the spec; Transactions has it.

## Verification

- `python manage.py test`: 352 tests OK.
- Edge headless, demo account, 1440px:
  - the month picker swaps `#dashboard` with no full navigation (0 frame navigations) and the address becomes `?month=2026-10`, then back to `?month=2026-11`;
  - October shows "Ended October with Rp754.010 left";
  - Tab onto a bar shows its tooltip ("4 Nov: Rp158.990") above the neighbouring bars.
- Edge with JavaScript off: the previous-month link does a normal page load to `?month=2026-10` with 31 bars; hovering a bar still shows the CSS tooltip.
- Screenshots at 1440px and 520px compared with the local Figma Make build of the Dashboard. Layout matches apart from the removed parts and STYLE.md copy; no horizontal scroll at 520px.

## Open before archiving

- The developer checks the Dashboard in a real browser across two months, then runs `/opsx:archive add-dashboard`.
- `docs/STYLE.md`, `docs/decisions.md` and `WORKPLAN.md` are updated locally only (`.gitignore`).
