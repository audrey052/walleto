# Changes: add-savings-goals (MVP 4)

This is the implementation log for this change. It lists what was created or modified, and where the result differs from `proposal.md`, `design.md` and `tasks.md`. Per-commit detail is in `openspec/commits/`.

- **Status:** implemented, not archived. Still open: the developer's real-browser check.
- **Date:** 2026-11-23
- **Tests:** 310 passing in about 9 s; 74 new in `finance/tests/test_goals.py`.
- **Validation:**
  - `openspec validate add-savings-goals --strict` passes.
  - `makemigrations --check` finds no changes.
  - `migrate finance 0004` and back to `0005` run cleanly.

## Commits

| Commit | Message | Record |
|---|---|---|
| this commit | feat: add savings goals that move money out of wallets, with progress, status and a detail chart | `add-savings-goals.md` |

## Routes

| Method | URL | Name | Purpose |
|---|---|---|---|
| GET | `/savings-goals/` | `finance:goals` | main goal card, other goals, completed |
| GET, POST | `/savings-goals/new/` | `finance:goal_create` | create (modal) |
| GET | `/savings-goals/<id>/` | `finance:goal_detail` | progress, chart, history |
| GET, POST | `/savings-goals/<id>/edit/` | `finance:goal_edit` | edit (modal) |
| GET, POST | `/savings-goals/<id>/add/` | `finance:goal_deposit` | add money from a wallet |
| GET, POST | `/savings-goals/<id>/withdraw/` | `finance:goal_withdraw` | move money back to a wallet |
| POST | `/savings-goals/<id>/main/` | `finance:goal_make_main` | make main goal |
| POST | `/savings-goals/<id>/complete/`, `/reopen/` | `finance:goal_complete`, `finance:goal_reopen` | complete (reached only), reopen |
| GET, POST | `/savings-goals/<id>/delete/` | `finance:goal_delete` | confirm, then soft delete (Rp0 only) |
| GET, POST | `/savings-goals/movement/<id>/delete/` | `finance:goal_movement_delete` | confirm, then remove a deposit or withdrawal |

`core:savings` and its placeholder view are removed. The section now points to `finance:goals`.

## Data

- Migration `finance.0005_savings_goals`:
  - `SavingsGoal`: target ≥ 1000 constraint; nullable `deadline`, `completed_at` and `deleted_at`; `is_main`.
  - `GoalContribution`: `kind` deposit/withdrawal, amount > 0 constraint, wallet PROTECT, indexes on `(user, date)` and `(wallet, kind)`.
- `Wallet.with_balance()` adds two subqueries: deposits out, withdrawals in.

## Files

### Backend
- `finance/models.py`: `SavingsGoal`, `GoalContribution`, `GoalQuerySet` (`for_user` hides deleted goals; `active`, `completed`, `with_saved`), `GoalContributionQuerySet`; goal movements in `with_balance()`.
- `finance/goals.py` (new): pure functions plus `summarize()`:
  - `progress`, `status` (integer cross-multiplication), `months_left`, `per_month` (ceiling);
  - `main_goal`, `saved_series`, `plan_series`.
- `finance/forms.py`: `GoalForm`, and `DepositForm` / `WithdrawForm` (wallet labels show balances).
- `finance/views_goals.py` (new): every goal view.
- `finance/urls.py`, `core/urls.py`, `core/views.py`, `core/sections.py`: section moved to `finance:goals`.
- `finance/history.py`: a third query for goal movements in the 30-day trend.
- `finance/views.py`: `set_aside` on the Wallets page.
- `finance/views_activity.py`: goal movements in the list (wallet filter, category filter, search) and in the CSV export.
- `finance/demo.py`: two demo goals, "Emergency fund" (on track) and "New laptop" (behind), with deposits inside the daily loop so balances stay ≥ 0.
- `finance/admin.py`: both models.

### Frontend
- `templates/finance/goals.html` (new):
  - the main goal card after Figma `.savings-feature`, with 9 ledger bars at the Figma heights;
  - the insight row;
  - Other goals, Completed, the empty state, and `#modal-root`.
- `templates/finance/goal_detail.html` (new): progress panel, ApexCharts chart (`json_script` data), history with remove.
- `templates/finance/_goal_fields.html`, `_goal_movement_fields.html` (Figma `.goal-modal-summary`), `_goal_delete_body.html`, `_goal_movement_delete_body.html`, `_goal_status.html`, `_goal_progress.html` (new).
- `templates/finance/wallets.html`: "Set aside in goals" line.
- `templates/finance/transactions.html`: goal rows linking to the goal; no link for a deleted goal.
- `static/js/app.js`: `goalChart` Alpine component.
- `static/vendor/apexcharts.min.js` (new, 3.54.1, MIT).

### Tests
- `finance/tests/test_goals.py` (new) covers:
  - balances, the trend query count, the transfer overdraft with goal money;
  - every calculation scenario and both series;
  - forms, views and the page;
  - detail page and chart data;
  - privacy, Wallets set-aside, Transactions rows, filters and CSV;
  - demo goals on four dates.
- `finance/tests/test_wallets_page.py`: trend query count 2 → 3.
- `core/tests.py`, `accounts/tests.py`: the placeholder test now uses Assistant; section URL lists.

### Documentation (local only: these files are in `.gitignore`)
- `docs/STYLE.md`: the Savings goals row of the page map.
- `WORKPLAN.md`: MVP 4 ticked, with the final model fields.
- `docs/decisions.md`: four decisions (money moves into goals, completing uses the money, soft delete, ApexCharts vendored).

## Differences from the plan

- **The spec's "On track" scenario had wrong arithmetic.** It said Rp2.000.000 saved on day 78 of 90 of a Rp3.000.000 goal is on track. 2.000.000 × 90 < 3.000.000 × 78, so that goal is behind. The first calculation test caught it. The scenario now uses Rp2.700.000, and "Behind" uses the same goal with Rp2.500.000.
- **Wallet balances are shown in the wallet dropdown** ("BCA · Rp7.842.500") instead of a separate list in the modal.
- **The main card's right column shows the percent** where Figma shows the decorative "01". The goal's start date replaces "SMALL STEPS. REAL PROGRESS." (docs/STYLE.md copy rules).
- **The main card has a "View history" link** next to "Edit goal", so the detail page is reachable from the card. The goal name links there too.

## Verification

- `python manage.py test`: 310 tests OK.
- Edge driven over the DevTools protocol with the demo account:
  - "New goal" modal opened and created a goal (toast "Goal created.");
  - "Add to this goal" listed the wallets with balances, refused Rp99.000.000 with "Not enough in BCA…", then saved Rp500.000 (toast "Added to New laptop.");
  - the detail page drew the ApexCharts SVG with both series.
- `/static/vendor/apexcharts.min.js` is served (200, 539 KB). A test checks that the other pages don't load it.
- Screenshots at 1440px compared with the local Figma Make build of Savings goals. The card layout, padding, ledger bars and insight row match. Copy follows docs/STYLE.md.
- The narrow layout stacks without sideways scrolling. Edge headless renders about 520px at minimum.
- The demo data was reset with `seed_demo` after the browser test.

## Open items before archiving

- The developer checks Savings goals, a goal detail page, Wallets ("Set aside in goals") and Transactions (goal rows) in a real browser, then runs `/opsx:archive add-savings-goals`.
