# Tasks

## 1. Models and balances

- [x] 1.1 Add `SavingsGoal` and `GoalContribution` with querysets (`for_user` excluding deleted, `active`, `completed`, `with_saved`), check constraints (target ≥ 1000, amount > 0), admin, and migration `finance.0005`; verify `makemigrations --check` is clean and `migrate finance 0004` / `0005` both run
- [x] 1.2 Extend `WalletQuerySet.with_balance()` with deposits out and withdrawals in (design decision 3); verify a test for the "Balance after saving" scenario (Rp7.242.500) and that the transfer overdraft test still passes
- [x] 1.3 Count goal movements in `finance/history.py` with one extra query; verify a trend test where a deposit three days ago lowers the last three points and the query count stays fixed

## 2. Goal calculations

- [x] 2.1 Write `finance/goals.py`: `progress`, `status`, `months_left`, `per_month`, `main_goal` (design decision 4); verify unit tests for every savings-goals scenario with numbers (25% / Rp4.500.000, reached, on track 2.700.000 × 90 ≥ 3.000.000 × 78, behind, past deadline, Rp750.000 a month for 8 months, nearest deadline, chosen main goal)
- [x] 2.2 Add `saved_series` and `plan_series` for the chart; verify tests for a series stepping on deposit dates, a withdrawal stepping down, and a plan line from Rp0 at the start to the target at the deadline

## 3. Forms and goal actions

- [x] 3.1 `GoalForm` (name rules, unique among active goals ignoring case, target ≥ Rp1.000, deadline after today unless unchanged on edit); verify form tests for each creation scenario
- [x] 3.2 `DepositForm` and `WithdrawForm` (active own wallets only, amount > 0, date not in the future and not before the start date, wallet balance / goal saved limits, `NOT_ENOUGH` message); verify form tests for deposit, not enough, withdraw, more than the goal holds, and another user's wallet
- [x] 3.3 Views and URLs for create, edit, deposit, withdraw, make main, complete, reopen, delete (soft, Rp0 only, with the "move it back first" message and withdraw link), and movement delete (refused if saved would go negative), with the toasts from the spec; verify view tests for each action, including deleting an empty goal leaving BCA and GoPay unchanged
- [x] 3.4 Privacy: every goal and movement view scoped to the user; verify tests that another user's goal, movement and wallet answer 404 or a form error

## 4. Savings goals page

- [x] 4.1 Move the section to `finance:goals` (remove `core:savings` and its placeholder view, update `core/sections.py` and the URL tests); verify the sidebar link opens the new page and existing shell tests pass
- [x] 4.2 `templates/finance/goals.html`:
  - the main goal card after the Figma `.savings-feature` (label, name, deadline and status, saved of target, progress, progress line or "Your goal, reached.", to go, "Add to this goal", 9 ledger lines; the card opens the goal);
  - the "Put aside … a month" row;
  - the other goals list with "Make main goal";
  - the Completed section, the empty state, and `#modal-root`.

  Verify page tests for several goals, nearest deadline, chosen main goal, reached, no goals, and completed.
- [x] 4.3 Modal templates for goal create/edit, deposit and withdraw (wallet select with balances, amount, date, note) and the confirmations; verify the modals open from the page in a real browser session and save through HTMX (the same check that found `99af433`)
- [x] 4.4 Headless screenshots at 1440px and 390px compared with the local Figma Make build of Savings goals; verify layout matches apart from STYLE.md copy

## 5. Goal detail page and chart

- [x] 5.1 Vendor `apexcharts@3.54.1` `dist/apexcharts.min.js` into `static/vendor/` and load it only from the detail template; verify the file is served and other pages don't include it
- [x] 5.2 `templates/finance/goal_detail.html`: progress, status, per month, actions, chart container with `json_script` data, and the history (From/To wallet, date, note, signed amount, delete); add the `goalChart` Alpine component to `static/js/app.js`; verify a page test for the history order and the chart JSON, and a browser check that the chart draws both lines

## 6. Wallets and Transactions

- [x] 6.1 Wallets balance panel: "Set aside in goals" with the active goals' saved total, linking to Savings goals, hidden at Rp0; verify tests for both wallets scenarios and that completed goals don't count
- [x] 6.2 Add goal movements to `_activity()` (wallet filter keeps them, category filter hides them, search on note and goal name) and render them as neutral rows linking to the goal (no link for a deleted goal); verify tests for "Deposit in the list", "Filters", and the summary excluding them from income and expenses
- [x] 6.3 CSV export rows with type "Savings", the route as description, the wallet's name, and an unsigned amount; verify the "Export a deposit" test

## 7. Demo data

- [x] 7.1 Demo goals in `finance/demo.py` (design decision 10); verify demo tests: at least two active goals with deposits from 1 September, one "On track" and one "Behind" on the demo date, every wallet ≥ Rp0, and a reset leaving other users' goals unchanged

## 8. Wrap-up

- [x] 8.1 Update `docs/STYLE.md` (Savings goals page-map row, chart colors), `WORKPLAN.md` MVP 4, and `docs/decisions.md` (wallet money moves into goals; completing uses the money; soft delete), then run `python manage.py test` and `openspec validate add-savings-goals --strict`; verify both pass
- [x] 8.2 Write `changes.md` and the commit record in `openspec/commits/`; verify the index in `openspec/commits/README.md` lists it

## Workflow follow-up

- Developer checks Savings goals and a goal detail page in a real browser, then archives with `/opsx:archive add-savings-goals`.
