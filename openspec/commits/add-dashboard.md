# Add the Dashboard

**Created:** 2026-11-24
**Last edited:** 2026-11-24
**Status:** Implemented
**Commit:** `f3a84a3` feat: add the dashboard
**Branch:** `main`, parent `352fe67`
**OpenSpec change:** `add-dashboard` (MVP 5), tasks 1.1–3.2
**Trigger:** `/opsx:apply add-dashboard` after the developer trimmed the proposal (no wallet filter, insight row or recent transactions).

## Why this is recorded here

The home page stops being a placeholder. A new service computes every Dashboard figure and will be reused by the Assistant (MVP 7). The `core:dashboard` route now calls a finance view.

## Context

- One function, `month_summary()`, returns every figure. It reuses the Transaction querysets and `month_budget`, so the numbers equal Transactions and Budget.
- The daily chart is HTML bars after the Figma `SpendingChart`, not ApexCharts, so it matches the design and works without JavaScript.
- Every figure covers all wallets, like the monthly plan.

## What is built

| Area | Change |
|---|---|
| `finance/summary.py` | `MonthSummary`: income and expenses, the month before, change in tenths of a percent, plan, remaining, projection, daily totals and chart, categories largest first with limit and percent; 5 queries regardless of data size |
| Projection | current month: "Enough for <n> days of meals at Rp50.000 a day" (remainder ÷ Rp50.000), "Not enough for a day of meals…", "Over your plan by …"; past months: "Ended <Month> with … left" or "… over plan" |
| `GET /` (`core:dashboard`) | `finance/views_dashboard.py::dashboard`, `?month=` like Transactions (no future months); HTMX swap of `#dashboard` with push URL |
| `templates/finance/dashboard.html` | Remaining with projection and progress (or "Set a monthly plan"), Total income and Total expenses with change vs. last month (no trend line), daily chart with dashed daily budget and tooltip, Where it goes linking to Transactions filtered by category |

## Requirements this establishes

1. **Dashboard figures come only from `month_summary()`.** Templates and the Assistant display them; they don't recompute.
2. **Dashboard numbers equal Transactions and Budget for the same month.** A test compares them.
3. **The summary's query count is fixed.** A test pins it at 5.

## Files changed

| File | Change |
|---|---|
| `finance/summary.py`, `finance/views_dashboard.py` | new |
| `core/urls.py`, `core/views.py` | route points at the new view; placeholder removed |
| `templates/finance/dashboard.html` | new |
| `static/src/app.css` | daily chart styles |
| `finance/tests/test_summary.py`, `finance/tests/test_dashboard.py` | new, 43 tests |
| `openspec/changes/add-dashboard/` | proposal, spec, design, tasks, changes.md |
| `openspec/commits/README.md` | `352fe67` filled in, this record |

## Verification

**Executed:**

- `python manage.py test`: 352 tests OK.
- `openspec validate add-dashboard --strict`: valid.
- Edge headless with the demo account at 1440px and 520px: month switching without reload and with the address updated, keyboard tooltip, no horizontal scroll; with JavaScript off the month links load normally and the tooltip still shows on hover.
- Compared with the local Figma Make build of the Dashboard.

**Fixed during implementation:**

- The tooltip was hidden behind the next bar; the hovered or focused bar is raised.
- At 520px the x-axis read "2425"; the fixed label next to today is left out.
- The chart panel left empty space under the chart; the chart now stretches to the panel height.

**Not executed:**

- The developer's own browser check.

## Known gaps

- **`docs/STYLE.md`, `docs/decisions.md` and `WORKPLAN.md` updated locally only** (`.gitignore`).
