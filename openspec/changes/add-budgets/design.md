# Design

## Context

MVP 2 added `Transaction` (with `kind` copied from the category, `in_month()` and `totals()`), `Transfer`, the Transactions page with its month picker (`_parse_month`, `_shift`, `?month=YYYY-MM`), the HTMX modal helpers (`render_form`, `redirect_after_save`) and the demo account. The Budget section is still the `core` placeholder (`core:budget`). Categories are the seven shared expense defaults and two income defaults (`user = NULL`); there is no UI yet for creating categories.

The design is the Budget section of the Figma Make file (`SqCtFlkW2pwTXgwnAeHSdb`, `src/App.tsx`; the same code is in `docs/design/figma-make-source/App.tsx`). It has one monthly total, an "Edit monthly plan" modal that says "Your category limits will adjust proportionally", an overview panel, and a category list with amber rows from 85%. The developer chose a hybrid: limits set per category as in WORKPLAN, plus the Figma "Edit monthly plan" that rescales them. They also chose the 85% line over 90%, and kept WORKPLAN's days left, per day, copy last month, red over state and Transactions warning.

## Goals / Non-Goals

**Goals:**
- Category limits the user controls, with a one-number shortcut to create or rescale them.
- Limits that always add up exactly to the plan total.
- Spent, remaining, per day and status computed by plain, tested Python, with edge cases (last day, February, leap year, rounding).
- A Budget page that matches the Figma design and the existing pages (month picker, modals, toasts).

**Non-Goals:**
- Editable default shares, rollover, per-wallet budgets, notifications outside the Transactions toast.

## Decisions

### 1. One row per category per month: `Budget(user, category, month, limit)`
`month` is a `DateField` holding the first day of the month; `limit` is a `BigIntegerField` (whole Rupiah) with a check constraint `limit >= 1000`; a unique constraint on `(user, category, month)`; `category` is a foreign key with `CASCADE`; `created_at` and `updated_at`. The form only accepts expense categories visible to the user. The monthly plan is not stored: it is `Sum("limit")` over the month's rows. Removing a limit deletes the row.
- Rejected: storing only a monthly total and deriving limits (the first version of this proposal). The user wants to set categories differently, for example more for Food and less for Health.
- Rejected: storing both the total and the limits. The two could disagree; the sum is cheap to compute.
- Rejected: `month` as two integer fields. A date sorts and filters naturally and matches `month_bounds()`.

### 2. Default shares on `Category.budget_share`, used only for the first split
A new `PositiveSmallIntegerField` on `Category` (default 10). Migration `0004` sets the defaults: Food & drinks 30, Shopping 15, Transport 15, Bills & utilities 15, Entertainment 10, Others 10, Health 5 (100 in total). These follow the Figma ratios and are adapted to the seven default categories. The shares are only used when the user enters one total for a month that has no limits. After that, the user's own limits are the proportions.
- Rejected: equal first split. Food would get the same limit as Health, which is unrealistic.
- Rejected: no first split (user must fill every category). The Figma flow starts from one number, and seven empty fields is a slow start.

### 3. Split and rescale with the largest remainder method
One helper, `distribute(total, weights) -> {key: amount}`: `amount_i = total × weight_i // sum(weights)`. The few Rupiah lost to rounding go one by one to the largest remainders (ties by category order). The first split uses the default shares as weights; a rescale uses the current limits as weights. So limits always add up exactly to the entered total.
- Rejected: plain rounding of each limit. The sum can be off by a few Rupiah, which a careful user would notice.
- Rejected: rescaling by adding the difference to one category. That does not match the design's "adjust proportionally".

### 4. Calculations in `finance/budgets.py`, pure functions plus two queries
- `distribute(total, weights)` (decision 3).
- `status(spent, limit) -> "normal" | "warning" | "over"`, using integer math: warning when `spent * 100 >= 85 * limit`, over when `spent > limit`. No floats near the threshold.
- `percent(spent, limit)`: rounded down, so 84.99% shows 84% and never looks like a warning that isn't there.
- `crossing(before, after, limit) -> "warning" | "over" | None` for the Transactions toast.
- `days_left(year, month, today)`: past month 0; current month `last_day - today.day + 1`; future month every day of that month (`calendar.monthrange`).
- `per_day(remaining, days_left)`: `remaining // days_left` when both are above zero, otherwise `None`.
- `month_budget(user, year, month, today)` returns a small dataclass. It holds the plan total, the budgeted rows (category, limit, spent, remaining, percent, status) sorted by spent with highest first, the unbudgeted categories with their spent amount, total spent (all expenses), days left and per day. It uses one query for the limits and one grouped query for spent per category: `Transaction.objects.for_user(user).in_month(y, m).expense().values("category").annotate(Sum("amount"))`.
- Rejected: computing statuses in SQL. Clearer and easier to test in Python, and a month has fewer than ten categories.

### 5. Budget page in `finance`, same month handling as Transactions
`finance:budget` at `/budget/?month=YYYY-MM` replaces `core:budget`; the section entry gets `url_name: "finance:budget"` and `match: "finance:budget"`. Month parsing reuses `_parse_month` and `_shift` from `views_activity`, moved into a small shared helper module. A new parameter allows one month ahead, because a plan is often made before the month starts. Transactions keeps "no future months".
- Rejected: allowing any future month. Months far ahead are empty and add nothing.

### 6. Modals follow the existing pattern
All forms render `components/modal_form.html` through `render_form`, save, and `redirect_after_save` back to the same month; without HTMX they are normal pages.
- `finance:budget_plan` (`/budget/plan/?month=…`): `PlanForm` with one `AmountField` (min 100.000). With no limits it creates rows by the first split; with limits it rescales them. All writes happen in one `transaction.atomic()` block. Toast "Your monthly spending plan has been updated."
- `finance:budget_category` (`/budget/category/<category_id>/?month=…`): `CategoryLimitForm` (min 1.000) with `update_or_create(user, category, month)`. The category is looked up with `Category.objects.for_user(user).expense()`, so another user's category or an income category answers 404. Toast "<Category> budget updated."
- `finance:budget_category_remove` (same address + `remove/`, `@require_POST`): deletes the user's row for that category and month. Toast "<Category> limit removed."
- `finance:budget_copy` (`/budget/copy/?month=…`, `@require_POST`): copies every row of the previous month only when the selected month has none. Toast "Copied October's budget."
- The heading button says "Edit monthly plan" when the month has limits, and "Set monthly plan" in the empty state.
- Rejected: addressing a limit by its own `Budget.pk`. Using category + month needs no lookup of row IDs, and works the same for "Set limit" on an unbudgeted category. Privacy is still enforced, because rows are always filtered by `user=request.user`.
- Rejected: copying over existing limits. That would need a confirmation step for little value. The button only shows on an empty month.

### 7. Transactions warning: compare before and after the save
In `transaction_create` and `transaction_edit`, the view looks up the user's limit for the category and month the expense ends up in. If there is one, the view computes that category's spent amount before saving, saves, computes it again, and calls `budgets.crossing(before, after, limit)`. A result adds `messages.warning(...)` with a link to `finance:budget?month=…`.
- Rejected: warning on every save while a category is at 85% or more. That would mean a toast on every coffee, and people would learn to ignore it.
- Rejected: Django signals. The warning is a UI message tied to the request, so it belongs in the view.

### 8. Toasts and progress bar
- `components/toasts.html` gets a warning style (amber icon and border) for `message.level_tag == "warning"`. The over message uses the error style (clay). Messages can carry a link through `extra_tags`, rendered as "Review your budget".
- `components/progress.html`: the warning line moves to 85 (`percent >= 85`). An optional `color` parameter sets the normal-state fill to the category color, as in the Figma rows. The template receives the already-rounded-down percent.
- docs/STYLE.md: progress and amber rows change from 90% to 85%, and the warning toast is added. The sign-in page illustration (`layouts/auth.html`, 87%) will now render amber. That is accepted, because it shows the feature.

### 9. Demo budgets
`build_demo(today)` creates limits for each of the three months with the first-split helper. Each total comes from the demo's actual expense level, computed from the generated data (for example 105% of the first full month's expenses, rounded to Rp100.000). The demo then nudges one or two categories so they differ from the default shares. A test checks that the current month has at least one category at 85% or more, instead of tuning numbers by hand.

## Risks / Trade-offs

- [Rescaling small limits can round them below Rp1.000] → `distribute` result is checked; the plan form rejects a total that would push any existing limit below Rp1.000, with a message asking for a larger total.
- [A future month can't have transactions, so its page shows all zeros] → Acceptable; it is the planning view, and it shows the full days of the month.
- [More rows than a single total: up to seven per month per user] → Negligible in size; one indexed query per page.
- [Two extra queries per transaction save] → Only for expenses whose category has a limit that month, and both are indexed by `(user, date)`.
