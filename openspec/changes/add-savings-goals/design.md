# Design

## Context

- See proposal.md for why. The requirements are in `specs/savings-goals`, `specs/wallets`, `specs/transactions` and `specs/demo-account`.
- **Balances.** `WalletQuerySet.with_balance()` adds one correlated subquery per kind of movement: income, expenses, transfers in and out. Several places read it:
  - the Wallets page;
  - the transfer overdraft check;
  - the transfer preview;
  - `finance/history.py`, the 30-day trend, which walks backwards from the current balances.
- **Activity.** `finance/views_activity.py::_activity()` merges transactions and transfers into one list. The page and the CSV export share that list.
- **Sections.** The Savings goals section is still a `core` placeholder (`core:savings`, `/savings-goals/`), as Budget was before MVP 3.
- **Front end.** There is no chart library in the repo yet. `static/vendor/` holds htmx and Alpine.

## Goals / Non-Goals

**Goals:**
- Goal movements change wallet balances everywhere a balance is read, with no second formula to keep in sync.
- Every figure a goal shows (saved, percent, status, per month, chart points) comes from pure functions with unit tests.

**Non-Goals:**
- No new app. Goals live in `finance`, because they move wallet money.
- No chart anywhere except the goal detail page. The Dashboard charts are MVP 5.

## Decisions

### 1. Two models; a withdrawal is a movement with a kind

The models:
- `SavingsGoal`: `user`, `name`, `target` (BigInteger, ≥ 1000), `deadline` (nullable), `start_date`, `position`, `completed_at` (nullable), `deleted_at` (nullable), `created_at`, `updated_at`.
- `GoalContribution`: `user`, `goal`, `wallet` (required, PROTECT), `kind` (`deposit` or `withdrawal`), `amount` (> 0, check constraint), `date`, `note`, `created_at`.

The goal's saved amount is the sum of deposits minus withdrawals. It is never stored.

*Rejected: signed amounts in one column.* A sign is easy to get wrong in forms and CSV, and a positive-amount check constraint can't apply to it.

*Rejected: making the wallet optional,* as WORKPLAN first listed. Money must come from somewhere for the wallet balances to stay true. That was the decision taken with the developer.

### 2. Deleting a goal is a soft delete

- `deleted_at` hides the goal everywhere. Its movements stay, so wallet balances can't shift.
- A goal that received from BCA and paid out to GoPay would otherwise move money between those two wallets when its rows disappeared.
- Delete is only allowed at Rp0 saved, so nothing is set aside for a deleted goal.
- The Transactions list still shows the movements of a deleted goal, under its name and without a link.

*Rejected: hard delete with cascade,* because it changes the balances of individual wallets. *Rejected: blocking delete once a goal has history,* because the user could then never remove a goal they abandoned.

### 3. Balances: two more subqueries in `with_balance()`

`with_balance()` gets two new terms:
- minus the wallet's deposits;
- plus the wallet's withdrawals.

These count every movement, including those of completed and deleted goals. A completed goal's money is "used" (savings-goals spec, "Complete a goal"), and a deleted goal holds Rp0.

Effects:
- The transfer overdraft check and the transfer preview pick this up without changes.
- The Wallets 30-day trend (`history.py`) that this decision extended was removed on 2026-11-24 at the developer's request.

### 4. Calculations in `finance/goals.py`

Pure functions over integers and dates:
- `progress(saved, target)` → percent rounded down, amount to go;
- `status(saved, target, start, deadline, today)` uses integer cross-multiplication, with no float;
- `months_left(today, deadline)` = `(deadline.year - today.year) * 12 + deadline.month - today.month + 1`;
- `per_month(to_go, months)` = ceiling division;
- `main_goal(goals)` returns the first goal by `position` (then oldest);
- `saved_series(start, today, movements)` gives the end-of-day saved amount;
- `plan_series(start, deadline, target)` gives the straight line, two points.

A `GoalQuerySet.with_saved()` annotation (`Sum` with `Case`) gives the list page every goal's saved amount in one query.

*Rejected: storing status or saved on the goal.* That would go stale whenever a movement is deleted.

### 5. Overdraft checks

- **Deposit:** the amount must not exceed the source wallet's balance, read with `with_balance()`. The message is the same `NOT_ENOUGH` text as transfers.
- **Withdrawal:** the amount must not exceed the goal's saved amount.
- **Deleting a deposit:** refused if it would make saved negative.
- **Deleting a withdrawal:** always allowed. It lowers the wallet's balance, the same as deleting a transfer, which may also leave a negative balance.

### 6. Pages and routes

All routes live in `finance/urls.py` under the existing `/savings-goals/` address:

| Method | URL | Purpose |
|---|---|---|
| GET | `/savings-goals/` | page: main goal card, other goals, completed |
| GET, POST | `/savings-goals/new/` | create (modal) |
| GET | `/savings-goals/<id>/` | detail: chart and history |
| GET, POST | `/savings-goals/<id>/edit/` | edit (modal) |
| GET, POST | `/savings-goals/<id>/add/` | deposit (modal) |
| GET, POST | `/savings-goals/<id>/withdraw/` | withdrawal (modal) |
| POST | `/savings-goals/order/` | save the drag-and-drop order (`order` = active goal ids, first = main) |
| POST | `/savings-goals/<id>/complete/`, `/reopen/` | complete, reopen |
| GET, POST | `/savings-goals/<id>/delete/` | confirm, then soft delete |
| GET, POST | `/savings-goals/movement/<id>/delete/` | confirm, then delete a movement |

- The section entry moves to `finance:goals`, and `core:savings` and its view are removed, as was done for Budget.
- Modals use `core/htmx.py` `render_form` / `redirect_after_save` and `components/modal_form.html`.
- Each page with modal links renders `<div id="modal-root">` (the lesson from fix `99af433`).

### 7. Main goal card after Figma

The layout follows `App.tsx` `.savings-feature` (grid `1.8fr 1fr`, 40px padding) and the `.insight-row` below it:
- The ledger lines are 9 bars, `round(min(1, saved/target) × 9)` of them filled.
- The poetic copy, the "01" number and the eyebrow sentence are left out (docs/STYLE.md). The eyebrow becomes the label "Main goal".
- The main goal is the first in the user's order (decision 11). There is no "Make main goal" button and no "Other goals" heading.

### 8. ApexCharts, vendored and only on the detail page

- `apexcharts@3.54.1` (`dist/apexcharts.min.js`) is copied to `static/vendor/` and loaded by the detail template only.
- The data goes through `json_script`. A small Alpine component `goalChart` builds two series: saved as a stepline, and plan as a line. It uses the forest and sage colors from docs/STYLE.md.
- Without JavaScript the chart area stays empty and the history list is still there.

*Rejected: a CDN script tag,* because the app serves its own vendor files and must work offline in development. *Rejected: an inline SVG like the wallet sparkline,* because the detail chart needs axes and tooltips, and the project stack names ApexCharts.

### 9. Activity merge

- `_activity()` adds a third queryset, goal movements in the month:
  - narrowed by `wallet` when a wallet filter is set;
  - `none()` under a category filter;
  - searched on the note and the goal name.
- The entries carry the kind `goal`.
- Template rows reuse the transfer row style with the "Savings goal" category.
- In the CSV export the type is "Savings", the description is the route, and the wallet column is the wallet's name.

### 10. Demo goals

`finance/demo.py` adds two goals starting on the first demo day:
- **"Emergency fund"**: target Rp10.000.000, deadline about 6 months out, with monthly deposits from BCA after each salary. Sized to be on track.
- **"New laptop"**: target Rp15.000.000, deadline about 4 months out, with small deposits from Bank Jago. Sized to be behind.

A test checks both statuses and that every wallet stays at Rp0 or more, as for demo budgets.

### 11. Goal order by drag and drop (revised after the first review)

- `SavingsGoal.position` replaces `is_main`. Migration `0006` numbers existing goals in the order the old rule gave: the chosen main goal first, then nearest deadline, then oldest.
- The page renders the main card and the other goals as siblings of one sortable list. SortableJS 1.15.2 (vendored like htmx, about 44 KB, Savings goals page only) handles mouse and touch dragging; native HTML drag and drop doesn't work on touch screens.
- The grip handle also moves a goal with the arrow keys, for keyboard users.
- Each move posts the full order to `/savings-goals/order/`. Ids that aren't the user's active goals are ignored. When the first goal changes, the page reloads so the new main goal gets the big card.

*Rejected: keeping "Make main goal" next to drag and drop.* That would be two ways to do the same thing, which is the duplication the developer asked to remove. *Rejected: native drag and drop,* because it doesn't work on touch screens.

## Risks / Trade-offs

- [Six correlated subqueries per wallet] → still one query per page. The wallets list is small (a handful per user). If it becomes slow, add an index on `GoalContribution(wallet, kind)`.
- [Soft delete adds a filter everywhere] → `GoalQuerySet.for_user()` excludes deleted goals by default. Movements are read through their own queryset, so the history stays intact.
- [Completing a goal "uses" its money, but no expense is recorded] → the monthly budget never sees the purchase. This was agreed: the money was set aside earlier, so it shouldn't count against a later month's budget. Recorded in `docs/decisions.md`.
- [ApexCharts adds about 500 KB] → loaded only on the goal detail page.

## Migration Plan

- `finance.0005` creates both tables. There is no data migration, because no existing row changes.
- Rollback: migrate `finance 0004`. The two tables are dropped, and wallet balances return to their previous formula automatically.
