# Changes: add-budgets (MVP 3)

Implementation log for this change: what was created or modified, and where the result differs from `proposal.md`, `design.md` and `tasks.md`. Per-commit detail is in `openspec/commits/`.

- **Status:** implemented and committed, not archived (open: task 7.2 real-browser check)
- **Date:** 2026-11-17
- **Tests:** 214 passing in about 4 s; 59 of them new (22 model and calculation, 34 page / modal / privacy / warning, 3 demo)
- **Validation:** `openspec validate add-budgets --strict` passes; `makemigrations --check` finds no changes

## Commits

| Commit | Message | Record |
|---|---|---|
| this commit | feat: add budgets with category limits, a proportional monthly plan and warnings | `add-budgets.md` |

The proposal, its revision to the hybrid model, and the implementation were made in one session and committed together.

## Routes

| Method | URL | Name | Purpose |
|---|---|---|---|
| GET | `/budget/?month=YYYY-MM` | `finance:budget` | Budget page (replaces `core:budget`) |
| GET, POST | `/budget/plan/?month=…` | `finance:budget_plan` | "Edit monthly plan" modal: first split or proportional rescale |
| GET, POST | `/budget/category/<id>/?month=…` | `finance:budget_category` | "Edit budget" / "Set limit" modal for one expense category |
| GET, POST | `/budget/category/<id>/remove/?month=…` | `finance:budget_category_remove` | GET asks for confirmation, POST removes the limit |
| POST | `/budget/copy/?month=…` | `finance:budget_copy` | Copy every limit of the previous month into an empty month |

## Data

- `Budget(user, category, month, limit, created_at, updated_at)`: unique `(user, category, month)`, check `limit >= 1000`, `month` normalised to day 1 on save.
- `Category.budget_share` (default 10). Migration `finance.0004_budgets` sets the shares of the seven default expense categories (30/15/15/15/10/10/5).

## Files

### Backend
- `finance/models.py`: `Budget`, `BudgetQuerySet` (`for_user`, `in_month`), `Category.budget_share`, `MIN_CATEGORY_LIMIT`, `MIN_PLAN_TOTAL`.
- `finance/migrations/0004_budgets.py`: new field, default shares, `Budget` table.
- `finance/budgets.py` (new): `distribute`, `status`, `percent`, `crossing`, `days_left`, `per_day`, `month_budget` (dataclasses `MonthBudget`, `BudgetRow`, `UnbudgetedRow`), `plan_limits`, `category_spent`, `limits_for`.
- `finance/months.py` (new): `parse_month` (with `allow_next`), `shift`, `month_param`, moved out of `views_activity.py`.
- `finance/forms.py`: `PlanForm` (min Rp100.000, rejects totals that push a limit below Rp1.000), `CategoryLimitForm` (min Rp1.000).
- `finance/views_budget.py` (new): the five views above.
- `finance/views_activity.py`: uses `months.py`; `_budget_watch` / `_budget_warning` add the warning or over toast after creating or editing an expense.
- `finance/urls.py`, `core/urls.py`, `core/views.py`, `core/sections.py`: Budget moves from the `core` placeholder to `finance:budget`.
- `finance/admin.py`: `BudgetAdmin`; `budget_share` shown on categories.
- `finance/demo.py`: `_build_budgets` gives the demo user limits for its three months, from the first month's spending + 5%; tightens one current-month category to about 90% when none is at 85% yet.

### Frontend
- `templates/finance/budget.html` (new): heading with month picker, overview panel, category rows, unbudgeted rows, empty state with copy.
- `templates/finance/_budget_plan_fields.html`, `_budget_limit_fields.html`, `_budget_remove_body.html` (new): modal bodies.
- `templates/components/progress.html`: warning from 85%; optional `color` for the normal fill.
- `templates/components/toasts.html`, `static/src/app.css`: `toast-warning` style and an optional "Review your budget" link.
- `templates/components/modal_form.html`, `form_page.html`: optional `delete_label` (used for "Remove limit").
- `templates/core/styleguide.html`: category-colored and 85% progress samples, warning and over toasts.

### Tests
- `finance/tests/test_budgets.py` (new): constraints, default shares, `distribute`, statuses and percent at the edges, crossing, days left (last day, Feb 2027, Feb 2028, past, future), per day, `month_budget`, privacy.
- `finance/tests/test_budget_views.py` (new): page, month handling, plan modal (first split, rescale, too small), category limit (set / change / remove / income 404), copy, privacy, Transactions warning.
- `finance/tests/test_demo.py`: demo budgets per month, something to notice on several dates, reset keeps others' budgets.
- `accounts/tests.py`: access tests point to `finance:budget`.

### Documentation (local only: these files are in `.gitignore`)
- `docs/STYLE.md`: 85% line, category-colored progress, rounded-down percent, warning toast.
- `WORKPLAN.md`: MVP 3 rewritten to the chosen model and ticked.
- `docs/decisions.md`: six budget decisions.

## Differences from the plan

- **Remove limit asks first.** Design decision 6 planned `@require_POST` for removing a limit. It follows the transaction-delete pattern instead: GET shows a confirmation in the modal, and only POST removes. A GET still never changes data, so the spec holds.
- **Over toast uses the error style.** The over message is sent at the error level so it shows in clay, as design decision 8 describes. The warning message uses the new amber `toast-warning`.
- **Category modal title.** A category without a limit gets the title "Set a limit for <Category>"; one with a limit gets "Edit budget". The spec names only "Edit budget".
- **Demo limits.** Instead of a total split by default shares and then nudged (design decision 9), limits come from each category's real spending in the first demo month plus 5%. This looks more like a person's own plan, and the "something to notice" rule is still checked by a test.

## Verification

- `python manage.py test`: 214 tests OK.
- `migrate finance 0003` and back to `0004` both run cleanly.
- Headless Edge screenshots with the demo account: Budget at 1440px (November with plan, October, December empty state with copy), at 390px inside an iframe (no sideways scroll, rows stack), the "Edit budget" modal, and the style guide.

## Open items before archiving

- Task 7.2: check the Budget page in a real browser at desktop and phone width (headless screenshots done).
- Then archive with `openspec archive add-budgets`.
