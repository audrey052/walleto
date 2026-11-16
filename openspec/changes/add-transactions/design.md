# Design

## Context

MVP 1 added `Wallet` (with `with_balance()` returning the starting balance), `Category` with nine shared defaults, `AmountField`, and the HTMX form helpers (`render_form`, `redirect_after_save`, `components/modal_form.html`). The Transactions section is still the `core` placeholder. The sign-in page shows a disabled "Try demo account" button.

## Goals / Non-Goals

**Goals:**
- Balances that are always right, computed by the database, and tested against hand-calculated values.
- A Transactions page that stays fast and correct with filters, day subtotals and pagination.
- A demo account a visitor can open in one click.

**Non-Goals:**
- Budgets, dashboard charts, AI quick add, CSV export.

## Decisions

### 1. Two models: `Transaction` and `Transfer`
`Transaction(user, wallet, category, kind, amount, date, description, note, source, created_at, updated_at)` and `Transfer(user, from_wallet, to_wallet, amount, date, note, created_at, updated_at)`. Amounts are positive `BigIntegerField`s with database check constraints (`amount > 0`, and `from_wallet <> to_wallet` for transfers). Foreign keys to wallets and categories use `on_delete=PROTECT`.
- Rejected: modelling a transfer as two linked transactions (an expense and an income). Simple to sum, but every income/expense report would have to exclude them, and editing one half could break the pair.

### 2. `kind` is stored, but always copied from the category
The form offers one category list grouped into Expense and Income; `kind` is set from the chosen category on save. Stored so that sums by kind don't need a join.
- Rejected: a separate Expense/Income toggle plus a category list. Two inputs that can disagree.

### 3. Balance with correlated subqueries
`with_balance()` annotates `balance = initial_balance + income − expense + transfers_in − transfers_out`, each part a `Subquery` with `Coalesce(Sum(...), 0)` filtered on the outer wallet.
- Rejected: `annotate(Sum("transactions__amount"))` over joins. Joining transactions and transfers in one query multiplies rows and gives wrong sums.
- Rejected: a stored balance column. It would drift whenever a transaction is edited or deleted.

### 4. One month per page; transfers merged in Python
The page is keyed by `?month=YYYY-MM`. Transactions and transfers for the month (after filters) are fetched in two queries, merged into one list sorted by date and creation time (newest first), and paginated with Django's `Paginator` (50 per page). Day subtotals come from one aggregate query grouped by date over the filtered transactions, so a day split across pages still shows its full subtotal. A month holds at most a few hundred entries, so merging in memory is cheap.
- Rejected: a SQL `UNION` of both tables. More complex to write and to filter, for no gain at this size.

### 5. Filters as a GET form with HTMX
The toolbar is a plain GET form. With HTMX, changes trigger `hx-get` on the page URL with `hx-select` of the results region and `hx-push-url="true"`, so the address always reflects the filters and the page also works without JavaScript. Search waits 300 ms after typing stops.
- Rejected: a separate JSON endpoint and client-side rendering. Duplicates the templates.

### 6. Forms only offer the user's own active wallets
`TransactionForm` and `TransferForm` limit the wallet querysets to `Wallet.objects.for_user(user).active()`, plus the wallets already on the record when editing. The category queryset is `Category.objects.for_user(user)`. Anything else fails as an invalid choice.

### 7. Date rules in Jakarta time
"Today" is `timezone.localdate()`. Dates after today are rejected. The month navigator never goes past the current month.

### 8. Deleting records is allowed
Transactions and transfers can be deleted after a confirmation modal; wallets still can't. A wrong entry is a mistake to remove, not history to keep.

### 9. Demo account
A fixed user `demo@walleto.app` with an unusable password. `seed_demo` (`finance/management/commands/seed_demo.py`) deletes that user's wallets, transactions and transfers and rebuilds them with a random generator seeded by the date, so the data is stable within a day. Expenses come from a list of Indonesian merchants with irregular amounts; salary arrives on the 1st; BCA tops up GoPay and OVO. The generator keeps every wallet's balance at or above zero by skipping an expense the wallet can't cover. `POST /demo/` (`@login_not_required`) creates the data if the demo user doesn't exist, signs the visitor in and redirects to the Dashboard.
- Rejected: a shared password shown on the sign-in page. Clumsier, and the password would end up in the repository.
- Accepted risk: visitors share the demo user and can change its data. `seed_demo` restores it; scheduling it is part of deployment (MVP 8).

## Risks / Trade-offs

- **Correlated subqueries per wallet** run four small sums per wallet row. Fine for a handful of wallets; indexes on `(wallet, kind)` and on the transfer wallet columns keep them fast.
- **Editing a starting balance** now silently shifts every later balance. Acceptable; the edit form says so.
- **Shared demo data** can be messed up by one visitor for the next. Mitigated by reseeding.
