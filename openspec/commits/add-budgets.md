# Add Budgets with Category Limits, a Proportional Monthly Plan and Warnings

**Created:** 2026-11-17
**Last edited:** 2026-11-17
**Status:** Implemented, with task 7.2 (real-browser pass) outstanding
**Commit:** this commit
**Branch:** `main`, parent `fc953ab`
**OpenSpec change:** `add-budgets` (MVP 3), proposal and tasks 1.1–7.4 except 7.2
**Trigger:** WORKPLAN MVP 3 and the Figma Make Budget section (`SqCtFlkW2pwTXgwnAeHSdb`); the developer chose the hybrid model (per-category limits plus a proportional "Edit monthly plan"), the 85% warning line, and all WORKPLAN extras.

## Why this is recorded here

New model and migration (`Budget`, `Category.budget_share`, `finance.0004`), five new routes, a new calculation module, the Budget section moving from the `core` placeholder to `finance`, and a shared-component change (progress bar amber from 85% instead of 90%).

## Context

- The first proposal stored one monthly total split by fixed shares. The developer asked to set each category themselves, so the change was revised before implementation: limits are stored per category, the plan is their sum, and "Edit monthly plan" rescales them.
- Default shares are only used for the first split of an empty month.
- Departures from `design.md` are listed in `openspec/changes/add-budgets/changes.md`: remove-limit asks for confirmation on GET (like deleting a transaction), and demo limits come from the first demo month's spending plus 5%.

## What is built

### Model

| Model | Fields | Rules |
|---|---|---|
| `Budget` | `user`, `category`, `month` (first day), `limit`, `created_at`, `updated_at` | unique `(user, category, month)`; `limit >= 1000` |
| `Category` | + `budget_share` (default 10) | defaults 30/15/15/15/10/10/5 set by migration |

### Routes

| Method | URL | Access | Purpose |
|---|---|---|---|
| GET | `/budget/?month=YYYY-MM` | signed in | Budget page, current month up to one month ahead |
| GET, POST | `/budget/plan/` | signed in | first split or proportional rescale |
| GET, POST | `/budget/category/<id>/` | own expense categories | set or change one limit |
| GET, POST | `/budget/category/<id>/remove/` | own limits | confirm, then remove |
| POST | `/budget/copy/` | signed in | copy last month's limits into an empty month |

### Modules

| Module | Job |
|---|---|
| `finance/budgets.py` | largest-remainder split, status / percent / crossing with integer math, days left, per day, `month_budget` |
| `finance/months.py` | `?month=` parsing shared by Transactions and Budget |
| `finance/views_budget.py` | page and modals |
| `finance/views_activity.py` | warning or over toast when a saved expense crosses 85% or 100% |

## Requirements this establishes

1. **The monthly plan is never stored.** It is the sum of the month's category limits.
2. **Budget status uses integer math and rounded-down percent.** Warning from 85%, over above 100%.
3. **Budget warnings fire only on crossing a line,** not on every expense above it.
4. **Every budget query is scoped to the user;** another user's category or limit answers 404.

## Files changed

| File | Change |
|---|---|
| `finance/models.py`, `finance/migrations/0004_budgets.py`, `finance/admin.py` | `Budget`, `budget_share`, admin |
| `finance/budgets.py`, `finance/months.py`, `finance/views_budget.py` | new |
| `finance/forms.py` | `PlanForm`, `CategoryLimitForm` |
| `finance/views_activity.py` | month helpers moved out; budget warning |
| `finance/urls.py`, `core/urls.py`, `core/views.py`, `core/sections.py` | Budget section moved to `finance:budget` |
| `finance/demo.py` | demo limits for three months |
| `templates/finance/budget.html`, `_budget_plan_fields.html`, `_budget_limit_fields.html`, `_budget_remove_body.html` | new |
| `templates/components/progress.html`, `toasts.html`, `modal_form.html`, `form_page.html`, `templates/core/styleguide.html`, `static/src/app.css` | 85% line, category color, warning toast, `delete_label` |
| `finance/tests/test_budgets.py`, `finance/tests/test_budget_views.py` | new |
| `finance/tests/test_demo.py`, `accounts/tests.py` | demo budgets; `finance:budget` |
| `openspec/changes/add-budgets/` | proposal, specs, design, tasks, changes |
| `openspec/commits/README.md`, `archive-add-transactions.md` | index and hash |

## Verification

**Executed:**

- `python manage.py test`: 214 tests OK (59 new).
- `makemigrations --check`: no changes; `migrate finance 0003` and forward again run cleanly.
- `openspec validate add-budgets --strict`: valid.
- Headless Edge screenshots with the demo account: Budget at 1440px (current, past and next month) and 390px, the edit modal, the style guide. A build of the Figma Make source was screenshotted at 1440px for comparison; layout matches, with the copy and type-size differences that docs/STYLE.md requires.

**Fixed during implementation:**

- Month names used `strftime`, which depends on the server locale; replaced with Django's `dateformat`.

**Not executed:**

- Real-browser pass (task 7.2).

## Known gaps

- **Task 7.2 is open.** The developer checks the page in a real browser before archiving.
- **Documentation updates are local only.** `docs/STYLE.md`, `docs/decisions.md` and `WORKPLAN.md` were updated but are in `.gitignore`.
