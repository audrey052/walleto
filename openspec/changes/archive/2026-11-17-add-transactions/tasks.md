# Tasks

## 1. Models and balances

- [x] 1.1 `Transaction` model with `kind` copied from the category, check constraint `amount > 0`, indexes on `(user, date)` and `(wallet, kind)`, `PROTECT` to wallet and category
- [x] 1.2 `Transfer` model with check constraints `amount > 0` and `from_wallet <> to_wallet`, `PROTECT` to both wallets
- [x] 1.3 Querysets: `for_user`, `in_month(year, month)`, `search(text)` for transactions; `for_user`, `in_month`, `touching(wallet)` for transfers
- [x] 1.4 Rewrite `WalletQuerySet.with_balance()` with four correlated subqueries (design decision 3)
- [x] 1.5 Migration `finance.0003`
- [x] 1.6 Admin for both models
- [x] 1.7 Model tests: balance formula against hand-computed values, negative balance, archived wallets keep history, constraints

## 2. Forms

- [x] 2.1 `TransactionForm`: description, amount (`AmountField`, > 0), date (default today, not future), category grouped by kind, wallet (own active, plus current when editing), note
- [x] 2.2 `TransferForm`: from, to (own active wallets), amount, date, note; different wallets; message when fewer than two active wallets
- [x] 2.3 Form tests: kind follows category, other users' wallets and categories rejected, future date, zero amount, same wallet

## 3. Transactions page

- [x] 3.1 Move the Transactions section from `core` to `finance:transactions` with `match: "finance:transaction"` (and transfers views marked as Transactions)
- [x] 3.2 Month handling: `?month=YYYY-MM`, default current month, previous/next links, no future months, invalid values fall back to the current month
- [x] 3.3 Month summary: income, expenses, net (transfers excluded), with the active filters applied
- [x] 3.4 Filters: wallet, category, search; HTMX `hx-get` with `hx-select`, `hx-push-url`, 300 ms debounce on search; works without JavaScript
- [x] 3.5 Merged list of transactions and transfers, newest first, 50 per page (first built with day groups; replaced by the Figma table in 3.8)
- [x] 3.6 Templates: summary, toolbar, grouped table (desktop) / list (mobile), transfer rows, empty states (no transactions, no matches with "Clear filters"), pagination
- [x] 3.7 View tests: month boundaries, summary numbers, each filter, transfers with wallet and category filters, search case-insensitive, pagination, HTMX partial response
- [x] 3.8 Match the Figma layout: month picker in the heading, toolbar with Export CSV, summary line, table with Transaction / Category / Wallet / Date / Amount, neutral row icons, sideways scroll on phones; font sizes from docs/STYLE.md
- [x] 3.9 CSV export of the filtered month (all pages) with formula protection, and tests

## 4. Add, edit, delete

- [x] 4.1 Transaction create, edit and delete views (modal or page, toasts) with `get_object_or_404(..., user=request.user)`
- [x] 4.2 Transfer create, edit and delete views, same pattern
- [x] 4.3 "Add transaction" and "Transfer" buttons on the Transactions page; "Transfer" on the Wallets page; rows open their edit modal
- [x] 4.4 Wallet cards: "View activity" link to `finance:transactions?wallet=<id>`; archived list shows real balances
- [x] 4.5 View tests: create/edit/delete with toasts, balances after each, privacy (404 for others' records), GET on delete only confirms

## 5. Demo account

- [x] 5.1 `seed_demo` command: demo user, five wallets, three months of data, deterministic per day, balances never below zero, other users untouched
- [x] 5.2 `POST /demo/` sign-in view (`@login_not_required`), enabled "Try demo account" button, toast
- [x] 5.3 Tests: data shape (wallets, salaries, no future dates), reset replaces only demo data, balances ≥ 0, demo sign-in creates data when missing, GET does nothing

## 6. Wrap-up

- [x] 6.1 Check Transactions and Wallets at 1440px and 390px against docs/STYLE.md and the Figma design (headless screenshots done; developer to do a real-browser pass)
- [x] 6.2 Write `changes.md` and a record per commit in `openspec/commits/`
- [x] 6.3 Update docs/decisions.md and README (how to load demo data)
- [x] 6.4 Run `openspec validate add-transactions --strict`
