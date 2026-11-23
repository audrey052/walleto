# Proposal

## Why

Walleto shows what was spent and what is left for the month, but not what the user is saving toward. People usually save for several things at once (an emergency fund, a trip, a laptop) and want to know whether they are on pace. Money set aside for a goal should also stop looking spendable in the wallets, or the user is tempted to spend it. MVP 4 in WORKPLAN.md.

## What Changes

- Add **savings goals**: a name, a target amount and an optional deadline. A user can have several active goals.
- **Adding money moves it out of a wallet.** "Add to this goal" takes an amount from one of the user's active wallets. The wallet balance drops, and the money is shown as set aside in goals. It is not an expense: budgets, income and expenses are unaffected, the same as a transfer.
  - A deposit can't be larger than the wallet's balance.
  - A **withdrawal** moves money from a goal back to a wallet, up to what the goal holds.
- **Progress is computed by code:**
  - saved (deposits minus withdrawals), percent, and the amount to go;
  - with a deadline, months left, the amount needed per month, and a status: **on track** or **behind** against a straight-line plan from the goal's start date to its deadline. A goal whose deadline has passed is **past deadline**.
- **Savings goals page,** replacing the placeholder:
  - The main goal uses the Figma card: name, saved "of" target, progress bar, "X% of the way there" or "Your goal, reached.", "Rp… to go", "Add to this goal", "Edit goal", and the ledger-lines illustration.
  - The main goal is the one the user picked, otherwise the one with the nearest deadline.
  - Below the card, a row "Put aside Rp… a month to reach your target by <month>" when the goal has a deadline.
  - A compact list of the other active goals, and a "Completed" section.
- **Goal detail page** with:
  - a line chart of the saved amount over time against the plan line;
  - the deposit and withdrawal history.
- **Goal actions:** create, edit, make main goal, mark complete (once reached) and reopen, delete (only when nothing is saved). Deposits and withdrawals can be deleted.
- **Wallets page:** the balance panel shows the amount set aside in goals. A wallet's balance now subtracts its deposits and adds its withdrawals, so the total balance stays spendable money.
- **Transactions page:** deposits and withdrawals appear as neutral rows, like transfers. They are excluded from income and expenses, and the CSV export includes them.
- The demo account gets goals with deposits.
- Copy follows docs/STYLE.md. The poetic lines in the Figma section ("A little intention today…", "SMALL STEPS. REAL PROGRESS.") are not used.

**Assumption:** marking a goal complete means its money was used for what it was saved for. It stays out of the wallets and leaves "set aside in goals". To get the money back instead, the user withdraws it before completing, or deletes the goal once it is empty.

Out of scope for this MVP:
- Automatic or recurring deposits.
- Interest or investment returns on saved money.
- Sharing a goal with another user.
- Goals in the topbar bell or on the Dashboard (MVP 5).
- AI savings advice (MVP 7).
- Goal images or custom icons.

## Capabilities

### New Capabilities
- `savings-goals`: goals, deposits and withdrawals, progress and status, the Savings goals page and the goal detail page, completing and deleting goals, and goal privacy.

### Modified Capabilities
- `wallets`: a wallet's balance counts goal deposits and withdrawals, and the balance panel shows the amount set aside in goals.
- `transactions`: goal deposits and withdrawals appear in the list and the CSV export as neutral entries.
- `demo-account`: demo data includes savings goals.

## Impact

- `finance/models.py`:
  - new `SavingsGoal` and `GoalContribution` models (a deposit or a withdrawal, always with a wallet);
  - `Wallet.with_balance()` includes goal movements.
- Migration `finance.0005`.
- New goal calculation module with unit tests, plus views, forms, URLs and templates for the page, the detail page and the modals.
- The Savings goals section moves from the `core` placeholder to `finance`.
- `finance/views.py`, `finance/history.py`, `templates/finance/wallets.html`: set-aside figure; the 30-day trend counts goal movements.
- `finance/views_activity.py` and the CSV export: goal rows.
- `finance/demo.py`: demo goals.
- New front-end dependency: ApexCharts, vendored under `static/vendor/` like htmx and Alpine. It is named in the project stack.
