# Tasks

## 1. Monthly summary service

- [x] 1.1 `finance/summary.py`: `MonthSummary`, `month_summary()` with income and expenses, the month before and the change in tenths, plan, remaining and `has_plan` from `month_budget`, daily totals, daily budget, and categories largest first with limit and percent; verify unit tests for "Plan and spending", "Change against last month", "Nothing last month", "Daily bars", "Daily budget line", and "Ordered by spending"
- [x] 1.2 Projection rules (`meal_days` at Rp50.000 a day, `over`, `ended_left`, `ended_over`); verify tests for "Days of meals", "Less than a day", "Over the plan" and "Past month"
- [x] 1.3 Figures match the other pages and the query count is fixed; verify a test comparing the summary with the Transactions page context (income, expenses) and `month_budget` (plan, categories) for the same month, plus an `assertNumQueries` test

## 2. Route and page

- [x] 2.1 `finance/views_dashboard.py::dashboard` with `?month=`; point `core:dashboard` at it and delete the placeholder view; verify tests for "Earlier month", "Future month", "Another user's spending", that sign-in still lands on `/`, and that the existing shell tests pass
- [x] 2.2 No trend lines on the income and expense cards (removed by the developer); `{% sparkline %}` is not restored
- [x] 2.3 `templates/finance/dashboard.html` after the Figma Dashboard:
  - heading with the month picker;
  - balance overview (Remaining with projection and progress, or no-plan state; Total income and Total expenses with change);
  - daily chart and Where it goes (no wallet filter, insight row or recent list).

  Verify page tests for "Plan and spending", "No plan", "Open a category" and "No limit".
- [x] 2.4 HTMX month switching (`hx-select="#dashboard"`, push URL) and the CSS tooltip on bars; verify in Edge that switching months swaps without a reload and that the address updates, and that the page still works with JavaScript off
- [x] 2.5 Screenshots at 1440px and narrow width compared with the local Figma Make build of the Dashboard; verify layout matches apart from STYLE.md copy

## 3. Wrap-up

- [x] 3.1 Update `docs/STYLE.md` (Dashboard page-map row), `WORKPLAN.md` MVP 5 and `docs/decisions.md` (summary service, HTML daily chart, no wallet filter or recent list), then run `python manage.py test` and `openspec validate add-dashboard --strict`; verify both pass
- [x] 3.2 Write `changes.md` and the commit record in `openspec/commits/`; verify the index lists it

## Workflow follow-up

- The developer checks the Dashboard in a real browser across two months, then archives with `/opsx:archive add-dashboard`.
- `add-savings-goals` is still waiting for its archive.
