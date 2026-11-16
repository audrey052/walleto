# Proposal

## Why

Wallets currently show only their starting balance. Walleto becomes useful once people can record money coming in and going out, move money between their own wallets, and trust that every balance reflects that history. This MVP adds those records, makes balances real, and gives the Transactions section its page. It also adds the demo account, so a visitor can try the app with three months of realistic data without registering.

## What Changes

- Add income and expense **transactions**: wallet, category, amount, date, description and an optional note.
- Add **transfers** between two of the user's wallets. A transfer moves money; it is neither income nor expense, so the total across wallets does not change.
- **Wallet balances are computed** from the starting balance, transactions and transfers. Balances may go below zero.
- Replace the Transactions placeholder with a page for one month at a time, laid out as in the Figma design: a month picker; a toolbar with search, wallet and category filters (updating without a page reload) and Export CSV; a summary line with the entry count, income and expenses; a table with Transaction, Category, Wallet, Date and Amount columns; pagination.
- Add, edit and delete transactions and transfers in modals, with a confirmation before deleting and a toast after every change.
- A "Transfer" action on the Wallets page, and a "View activity" link on each wallet card that opens its transactions.
- A `seed_demo` management command and a working "Try demo account" button on the sign-in page.

Out of scope for this MVP:
- Budgets and the budget warning when a transaction pushes a category over 90% (MVP 3).
- Quick add in plain language (MVP 6).
- Recurring transactions, attachments, multiple currencies.

## Capabilities

### New Capabilities
- `transactions`: recording, listing, filtering, editing and deleting income and expenses.
- `transfers`: moving money between the user's own wallets.
- `demo-account`: the shared demo user, its data, and signing in to it.

### Modified Capabilities
- `wallets`: the balance shown on cards and in the total now includes transactions and transfers; wallet cards link to their activity; archived wallets can't receive new transactions or transfers.

## Impact

- `finance/models.py`: new `Transaction` and `Transfer` models with `on_delete=PROTECT` to wallets and categories; `WalletQuerySet.with_balance()` rewritten with database subqueries.
- New migration `finance.0003`.
- New views, forms, URLs and templates for transactions and transfers; Transactions moves from the `core` placeholder to `finance:transactions`.
- `accounts`: a demo sign-in view; `finance/management/commands/seed_demo.py`.
- No new dependencies.
