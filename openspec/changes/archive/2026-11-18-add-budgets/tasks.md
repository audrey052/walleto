# Tasks

## 1. Model and shares

- [x] 1.1 `Budget` model (`user`, `category` CASCADE, `month` = first of month, `limit` BigInteger, `created_at`, `updated_at`) with unique `(user, category, month)`, check `limit >= 1000`, `BudgetQuerySet.for_user()` and `in_month()`, and a `save()` that normalises `month` to day 1; verified by model tests for both constraints
- [x] 1.2 `Category.budget_share` (`PositiveSmallIntegerField`, default 10)
- [x] 1.3 Migration `finance.0004`: both fields, plus a data step that sets the default shares (Food & drinks 30, Shopping 15, Transport 15, Bills & utilities 15, Entertainment 10, Others 10, Health 5) with a reverse step; verified by `migrate` and `migrate finance 0003` both running cleanly
- [x] 1.4 Register `Budget` in `finance/admin.py` (list by user, month and category)

## 2. Calculations (`finance/budgets.py`)

- [x] 2.1 `distribute(total, weights)` using the largest remainder method (design decision 3); tests: 8.000.000 by default shares gives Food & drinks 2.400.000, 8.000.001 and 100.003 add up exactly, rescale 3.000.000 / 1.000.000 to 6.000.000 gives 4.500.000 / 1.500.000
- [x] 2.2 `status`, `percent` (rounded down) and `crossing(before, after, limit)` with integer math; tests at 84.99%, exactly 85%, exactly 100%, 100% + Rp1, zero spent, and each crossing case from the transactions spec delta
- [x] 2.3 `days_left(year, month, today)` and `per_day(remaining, days_left)`; tests for the middle of the month, the last day, 1 Feb 2027 (28), 1 Feb 2028 (29), past month (0), future month (full), nothing remaining (`None`)
- [x] 2.4 `month_budget(user, year, month, today)`; tests: plan total = sum of limits, only expenses in the month count (31 Oct excluded), transfers and income excluded, archived wallets included, unbudgeted spending in total spent and in the unbudgeted list, rows sorted by spent, over-plan remaining is negative
- [x] 2.5 Privacy test: another user's expenses and limits never affect `month_budget` for the first user

## 3. Budget page

- [x] 3.1 Move the shared month helpers (`_parse_month`, `_shift`, `_month_param`) from `views_activity.py` into `finance/months.py` with an `allow_next` option; existing Transactions tests still pass, new tests for one month ahead and invalid values
- [x] 3.2 `finance:budget` view and URL at `/budget/`; point the Budget section in `core/sections.py` to it with `match: "finance:budget"`; remove `core:budget` and its placeholder view; verified by the app-shell sidebar test and a 200 response
- [x] 3.3 Template `finance/budget.html`, heading: title, subtitle, month picker (next arrow disabled at one month ahead), and an "Edit monthly plan" button when the month has limits
- [x] 3.4 Overview panel as in Figma: eyebrow "YOUR MONTHLY SPENDING PLAN", plan total, "Rp… left to spend in November 2026" (or "Rp… over plan"), "Spent so far" percent, progress bar, "Rp… of Rp…", days left and "Rp… a day" when available
- [x] 3.5 Category list "A place for every Rupiah": icon, name, status line ("A little breathing room" / "Getting close to your limit" / "Over by Rp…"), progress bar in the category color (amber / clay by status), "Rp… of Rp…", percent, edit action; then unbudgeted categories with spent, "No limit set" and "Set limit"; responsive at 390px with no sideways scroll
- [x] 3.6 Empty state for a month without limits: "Set monthly plan", plus "Copy last month's budget" when the previous month has limits
- [x] 3.7 View tests: page numbers match `month_budget`, empty state with and without the copy button, invalid month falls back, next month allowed, two months ahead falls back

## 4. Modals: plan, category limit, remove, copy

- [x] 4.1 `PlanForm` (`AmountField`, min 100.000, "The plan must be at least Rp100.000.") and `CategoryLimitForm` (min 1.000, "The limit must be at least Rp1.000.")
- [x] 4.2 `finance:budget_plan` view: modal "Give your month a plan." with the note and current total; first split when empty, rescale when not, in one atomic block; rejects a total that would push a limit below Rp1.000; toast; redirect to the same month; works without HTMX
- [x] 4.3 `finance:budget_category` view: "Edit budget" modal for one expense category (looked up with `for_user(user).expense()`), `update_or_create`, toast "<Category> budget updated."; also serves "Set limit" for unbudgeted categories
- [x] 4.4 `finance:budget_category_remove` (`@require_POST`) with a "Remove limit" button in the edit modal, toast "<Category> limit removed."
- [x] 4.5 `finance:budget_copy` (`@require_POST`): copy every row of the previous month only into an empty month, toast "Copied October's budget."; nothing happens when there is nothing to copy or the month has limits
- [x] 4.6 View tests: first split, rescale keeps unbudgeted categories empty, too-small plan and limit, set / change (still one row) / remove a limit, income category gives 404, copy creates the same limits, copy does nothing on GET / non-empty month / empty previous month
- [x] 4.7 Privacy tests: edit, remove, plan and copy never touch another user's limits; another user's category ID answers 404

## 5. Shared components and Transactions warning

- [x] 5.1 `components/progress.html`: warning from 85%, optional `color` for the normal fill; update the styleguide samples; check the styleguide page and the sign-in illustration render as expected
- [x] 5.2 `components/toasts.html`: amber warning style and an optional link ("Review your budget"); verified on the styleguide page
- [x] 5.3 In `transaction_create` and `transaction_edit`, when the category has a limit that month, compute spent before and after the save and add the warning or over toast through `budgets.crossing` (design decision 7)
- [x] 5.4 Tests: crossing 85% shows the warning text, going over shows the over text, already in warning shows nothing, no plan shows nothing, category without a limit shows nothing, income shows nothing, an edit that moves an expense into another category warns for the new one

## 6. Demo data

- [x] 6.1 `build_demo(today)` creates limits for each of the three months, sized from the generated expenses (design decision 9); `seed_demo` reset replaces only demo limits
- [x] 6.2 Tests: limits for the right three months, at least one current-month category at warning or over, other users' limits untouched after reset

## 7. Wrap-up

- [x] 7.1 Update docs/STYLE.md (85% line, category-colored progress, warning toast) and WORKPLAN.md MVP 3 to the chosen model (category limits + proportional plan, 85%)
- [x] 7.2 Check the Budget page at 1440px and 390px against docs/STYLE.md and the Figma Budget section, with the demo account (headless screenshots at 1440px and 390px; row spacing and column widths refined to the Figma values on 2026-11-18; closed at the developer's request)
- [x] 7.3 Write `changes.md` and a record per commit in `openspec/commits/`
- [x] 7.4 Update docs/decisions.md (category limits with proportional plan, default shares only for the first split, 85% line, warnings only on crossing) and run `python manage.py test` and `openspec validate add-budgets --strict`

## Workflow follow-up

- After the "Done when" of MVP 3 is met, run `openspec archive add-budgets`.
