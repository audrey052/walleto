# Add Savings Goals That Move Money Out of Wallets, with Progress, Status and a Detail Chart

**Created:** 2026-11-23
**Last edited:** 2026-11-23
**Status:** Implemented, with the developer's real-browser check outstanding
**Commit:** `b8ac963` feat: add savings goals that move money out of wallets, with progress, status and a detail chart
**Branch:** `main`, parent `99af433`
**OpenSpec change:** `add-savings-goals` (MVP 4), proposal and tasks 1.1–8.2
**Trigger:** WORKPLAN MVP 4 and the Figma Make Savings goals section (`SqCtFlkW2pwTXgwnAeHSdb`). The developer agreed that:
- deposits move money out of a wallet;
- a user can have several goals, with the Figma card used for the main one;
- a goal can be on track or behind against a linear plan;
- a goal can be completed.

## Why this is recorded here

This commit adds:
- two models and a migration;
- a change to the wallet balance formula, which every balance reader uses;
- eleven routes, with the Savings goals section moving from the `core` placeholder to `finance`;
- a new vendored front-end dependency (ApexCharts);
- goal rows in Transactions and its CSV export.

## Context

- The proposal and design were written on 2026-11-18. The developer reviewed them and asked to start MVP 4.
- Departures from the plan are in `openspec/changes/add-savings-goals/changes.md`. The main one: the spec's "On track" example had wrong arithmetic, which the first calculation test caught and which was corrected in the spec.

## What is built

### Models

| Model | Fields | Rules |
|---|---|---|
| `SavingsGoal` | `user`, `name`, `target`, `deadline`, `start_date`, `is_main`, `completed_at`, `deleted_at` | target ≥ 1000; saved amount never stored; deleted goals hidden by `for_user` |
| `GoalContribution` | `user`, `goal`, `wallet`, `kind`, `amount`, `date`, `note` | amount > 0; wallet PROTECT |

### Routes

| Method | URL | Purpose |
|---|---|---|
| GET | `/savings-goals/` | main goal, other goals, completed |
| GET | `/savings-goals/<id>/` | detail, chart, history |
| GET, POST | `/savings-goals/new/`, `<id>/edit/`, `<id>/add/`, `<id>/withdraw/`, `<id>/delete/`, `movement/<id>/delete/` | modals |
| POST | `<id>/main/`, `<id>/complete/`, `<id>/reopen/` | actions |

### Modules

| Module | Job |
|---|---|
| `finance/goals.py` | progress, status, months left, per month, main goal, chart series |
| `finance/views_goals.py` | pages and modals |
| `static/vendor/apexcharts.min.js` | ApexCharts 3.54.1, detail page only |

## Requirements this establishes

1. **A wallet's balance subtracts goal deposits and adds withdrawals.** Completed and deleted goals included.
2. **Goal movements are never income or expenses** and never count toward a budget.
3. **A deleted goal keeps its movements,** so no wallet balance changes when a goal is deleted.
4. **Goal status uses integer cross-multiplication;** per month rounds up to the next Rupiah.
5. **Every goal query is scoped to the user;** another user's goal or movement answers 404.

## Files changed

| File | Change |
|---|---|
| `finance/models.py`, `finance/migrations/0005_savings_goals.py`, `finance/admin.py` | models, balance formula, admin |
| `finance/goals.py`, `finance/views_goals.py` | new |
| `finance/forms.py` | `GoalForm`, `DepositForm`, `WithdrawForm` |
| `finance/history.py`, `finance/views.py`, `finance/views_activity.py` | trend, set-aside figure, Transactions rows and CSV |
| `finance/urls.py`, `core/urls.py`, `core/views.py`, `core/sections.py` | section moved to `finance:goals` |
| `finance/demo.py` | two demo goals |
| `templates/finance/goals.html`, `goal_detail.html`, `_goal_*.html` | new |
| `templates/finance/wallets.html`, `transactions.html` | set-aside line, goal rows |
| `static/js/app.js`, `static/vendor/apexcharts.min.js` | `goalChart`, chart library |
| `finance/tests/test_goals.py` | new (74 tests) |
| `finance/tests/test_wallets_page.py`, `core/tests.py`, `accounts/tests.py` | query count, placeholder and section lists |
| `openspec/changes/add-savings-goals/` | proposal, specs, design, tasks, changes |
| `openspec/commits/README.md`, `fix-budget-modal-root.md` | `99af433` filled in, this record |

## Verification

**Executed:**

- `python manage.py test`: 310 tests OK (74 new).
- `makemigrations --check`: no changes. `migrate finance 0004` and forward again run cleanly. `openspec validate add-savings-goals --strict`: valid.
- Edge driven over the DevTools protocol with the demo account:
  - create a goal;
  - add money, including the overdraft refusal;
  - open the detail page and check that the chart draws both series.
- Screenshots at 1440px compared with the local Figma Make build.

**Fixed during implementation:**

- The spec scenario "On track" (Rp2.000.000 of Rp3.000.000 on day 78 of 90) was behind by its own formula. The scenario was corrected to Rp2.700.000.
- A full-page screenshot mode laid the page out under the sidebar. Screenshots were re-taken in a tall window. The page itself was fine.

**Not executed:**

- Real-browser pass by the developer.

## Known gaps

- **Real-browser check is open** before archiving.
- **`docs/STYLE.md`, `docs/decisions.md` and `WORKPLAN.md` updates are local only** (`.gitignore`).
