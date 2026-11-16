# Tasks

## 1. Models and balances

- [ ] 1.1 `Transaction` model with `kind` copied from the category, check constraint `amount > 0`, indexes on `(user, date)` and `(wallet, kind)`, `PROTECT` to wallet and category
- [ ] 1.2 `Transfer` model with check constraints `amount > 0` and `from_wallet <> to_wallet`, `PROTECT` to both wallets
- [ ] 1.3 Querysets: `for_user`, `in_month(year, month)`, `search(text)` for transactions; `for_user`, `in_month`, `touching(wallet)` for transfers
- [ ] 1.4 Rewrite `WalletQuerySet.with_balance()` with four correlated subqueries (design decision 3)
- [ ] 1.5 Migration `finance.0003`
- [ ] 1.6 Admin for both models
- [ ] 1.7 Model tests: balance formula against hand-computed values, negative balance, archived wallets keep history, constraints

## 2. Forms

- [ ] 2.1 `TransactionForm`: description, amount (`AmountField`, > 0), date (default today, not future), category grouped by kind, wallet (own active, plus current when editing), note
- [ ] 2.2 `TransferForm`: from, to (own active wallets), amount, date, note; different wallets; message when fewer than two active wallets
- [ ] 2.3 Form tests: kind follows category, other users' wallets and categories rejected, future date, zero amount, same wallet

## 3. Transactions page

- [ ] 3.1 Move the Transactions section from `core` to `finance:transactions` with `match: "finance:transaction"` (and transfers views marked as Transactions)
- [ ] 3.2 Month handling: `?month=YYYY-MM`, default current month, previous/next links, no future months, invalid values fall back to the current month
- [ ] 3.3 Month summary: income, expenses, net (transfers excluded), with the active filters applied
- [ ] 3.4 Filters: wallet, category, search; HTMX `hx-get` with `hx-select`, `hx-push-url`, 300 ms debounce on search; works without JavaScript
- [ ] 3.5 Merged list of transactions and transfers, newest first, 50 per page, day groups with full-day subtotals from one aggregate query
- [ ] 3.6 Templates: summary, toolbar, grouped table (desktop) / list (mobile), transfer rows, empty states (no transactions, no matches with "Clear filters"), pagination
- [ ] 3.7 View tests: month boundaries, summary numbers, day subtotals across pages, each filter, transfers with wallet and category filters, search case-insensitive, pagination, HTMX partial response

## 4. Add, edit, delete

- [ ] 4.1 Transaction create, edit and delete views (modal or page, toasts) with `get_object_or_404(..., user=request.user)`
- [ ] 4.2 Transfer create, edit and delete views, same pattern
- [ ] 4.3 "Add transaction" and "Transfer" buttons on the Transactions page; "Transfer" on the Wallets page; rows open their edit modal
- [ ] 4.4 Wallet cards: "View activity" link to `finance:transactions?wallet=<id>`; archived list shows real balances
- [ ] 4.5 View tests: create/edit/delete with toasts, balances after each, privacy (404 for others' records), GET on delete only confirms

## 5. Demo account

- [ ] 5.1 `seed_demo` command: demo user, five wallets, three months of data, deterministic per day, balances never below zero, other users untouched
- [ ] 5.2 `POST /demo/` sign-in view (`@login_not_required`), enabled "Try demo account" button, toast
- [ ] 5.3 Tests: data shape (wallets, salaries, no future dates), reset replaces only demo data, balances ≥ 0, demo sign-in creates data when missing, GET does nothing

## 6. Wrap-up

- [ ] 6.1 Check Transactions and Wallets at 1440px and 390px against docs/STYLE.md and the Figma design
- [ ] 6.2 Write `changes.md` and a record per commit in `openspec/commits/`
- [ ] 6.3 Update docs/decisions.md and README (how to load demo data)
- [ ] 6.4 Run `openspec validate add-transactions --strict`
