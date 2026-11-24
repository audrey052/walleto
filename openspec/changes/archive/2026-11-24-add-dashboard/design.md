# Design

## Context

- See proposal.md for why. The requirements are in `specs/dashboard`.
- **Existing building blocks:**
  - `finance/budgets.py::month_budget(user, year, month, today)` returns the plan, spent per category, category limits and percent (rounded down);
  - `TransactionQuerySet.in_month()`, `.income()`, `.expense()` and `.totals()`;
  - `finance/months.py` (`parse_month`, `shift`, `month_param`);
  - the month picker markup on Transactions and Budget;
  - HTMX partial swaps with `hx-select`, as on Transactions.
- **Home route.** `/` is `core:dashboard`, a placeholder view. The name is referenced 19 times, including the sign-in redirect.
- **Figma reference:** `App.tsx` page "Dashboard":
  - `.overview-toolbar` (eyebrow and wallet select; the select is not built), `.balance-overview` (Remaining with projection and progress, then two secondary metrics; their `MiniTrend` lines are not built, removed by the developer);
  - `.chart-category-grid` (`SpendingChart`, HTML bars with a dashed `budget-line`; "Where it goes" category rows with progress and percent);
  - `.insight-row` and `.recent-panel` (neither is built; removed by the developer).

## Goals / Non-Goals

**Goals:**
- One function computes every figure. The view and the Assistant (MVP 7) only read its result.
- Same numbers as Transactions and Budget, by reusing their querysets and `month_budget` rather than re-deriving them.
- The layout matches the Figma Dashboard.

**Non-Goals:**
- No caching. A month is a few hundred rows, and the summary costs a fixed number of queries.
- No client-side state beyond HTMX swaps and the chart tooltip.

## Decisions

### 1. `finance/summary.py::month_summary(user, year, month, today)`

It returns a frozen dataclass `MonthSummary`:

| Field | Meaning |
|---|---|
| `income`, `expense` | totals for the month |
| `prev_income`, `prev_expense`, `income_change_tenths`, `expense_change_tenths` | the month before, and the change in tenths of a percent (`None` when the month before is 0) |
| `plan`, `plan_spent`, `remaining`, `has_plan` | from `month_budget` |
| `projection` | a small value object: `kind` (`meal_days`, `over`, `ended_left`, `ended_over`), plus `days` and `amount` |
| `daily` | `[(date, expense)]` for every day of the month |
| `daily_budget` | `plan // days_in_month`, or `None` |
| `categories` | `[CategoryLine(category, spent, limit or None, percent or None)]`, largest first |

- All arithmetic is integer:
  - change = `round((cur - prev) * 1000 / prev)` tenths, done with integer division and half-up rounding;
  - share and percent are rounded down.
- Daily totals come from one `values("date").annotate(Sum)` query, and this month's and last month's income and expenses from one query with conditional sums.

*Rejected: computing in the template or view.* The Assistant needs the same figures without HTML.

### 2. Projection rules

For the current month:
- `remaining >= 0` gives `meal_days` with `days = remaining // DAILY_MEAL` (`DAILY_MEAL = 50_000`, a flat amount the developer chose; the line no longer uses the spending pace);
- `remaining < 0` gives `over`.

For past months, `ended_left` or `ended_over` from the remainder. All of it is pure and tested with the spec's numbers.

### 3. No wallet filter, no recent list

- Every figure covers all of the user's wallets, which is also what the monthly plan covers. So the category percent never mixes one wallet's spending with an all-wallet limit.
- The Figma wallet select and recent panel are left out at the developer's request. Transactions already has both a wallet filter and the full list.

### 4. Daily chart as server-rendered HTML bars

- The Figma `SpendingChart` is HTML: a y-axis with five labels, grid lines, a dashed `budget-line` with its amount, and one button per day whose height is a percent of the max.
- The template renders the same structure. Heights come from the view (`max(daily, daily_budget, 1)`, rounded to a whole percent).
- Each bar is a `<button>` with an `aria-label` ("12 Nov: Rp99.500"). A CSS tooltip shows on `:hover` and `:focus-visible`.
- Today's bar gets the current style; future days in the current month are empty cells.

*Rejected: ApexCharts* (vendored for goals). It would draw a different look from the Figma bars and needs JavaScript to show anything. Plain HTML matches the design and works without JavaScript.

### 5. Trend lines

- None. The income and expense cards show the total and the change against last month only; the developer removed Figma's `MiniTrend` lines on 2026-11-24.
- `{% sparkline %}` stays deleted (it went with the Wallets trend column).

### 6. Route, month and filter

- `finance/views_dashboard.py::dashboard`; `core:dashboard` (path `""`) points to it, and `core/views.py::dashboard` is deleted.
- `?month=` uses `parse_month` (no next month).
- The picker and the filter links use `hx-get` with `hx-select="#dashboard"`, `hx-target="#dashboard"`, `hx-swap="outerHTML"` and `hx-push-url="true"`, so the month changes without a full reload. They are plain links and a GET form without JavaScript.
- Category rows link to `finance:transactions?month=…&category=…`. The page has no modals.

### 7. Copy (docs/STYLE.md)

- Heading "Dashboard" with the section subtitle; no "YOUR MONTH AT A GLANCE".
- Labels: "Remaining this month", "Total income", "Total expenses", "vs. last month", "Daily spending" (subtitle "Expenses per day"), "Daily budget", "Where it goes" (subtitle "Spending by category").
- Projection lines as in the spec. "A little room to breathe…" is not used.
- No insight row: the Figma "A small observation: … Let's take a look" line is left out.

## Risks / Trade-offs

- [Rp50.000 a day is fixed in code] → it is the developer's own figure; a per-user setting can come later.
- [Many queries on one page] → a fixed set (two-month totals, daily, budget), regardless of data size. A test pins the count.

## Migration Plan

No data migration. Deploy is code only. Rollback restores the placeholder view.
