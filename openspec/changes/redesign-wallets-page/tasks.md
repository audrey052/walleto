# Tasks

## 1. Data for the page

- [x] 1.1 `finance/history.py` `balance_history(wallets, today, days=30)` from current balances plus two queries (design decision 2); tests: trend follows an expense, a transfer in and out, no activity gives a flat line, oldest first, query count stays fixed with five wallets
- [x] 1.2 `wallet_list` context: `breakdown` by type (Rp0 for empty types, sums equal the total), `history`, `date_range`, `recent_transfers` (three newest); view tests for each
- [x] 1.3 Remove `Wallet.monogram` and its tests; keep `color`

## 2. Wallets page template

- [x] 2.1 `{% sparkline values %}` template tag (120×32 SVG, baseline, end dot, flat series at mid-height) with a unit test
- [x] 2.2 Heading: title, STYLE.md subtitle, "Add wallet" (secondary) and "Transfer money" (primary, disabled with fewer than two active wallets)
- [x] 2.3 Balance panel per `.accounts-balance`: tinted left column with "TOTAL BALANCE", amount, "Across N wallets · As of <date>"; right column with Bank accounts / E-wallets / Cash
- [x] 2.4 "Your wallets" heading with count and date range; table with column headings, rows (name, type, sparkline, balance, chevron) linking to activity, hover/focus edit and archive icons (always shown below 768px); footer "Add another wallet" / "All balances in Indonesian Rupiah"; phone layout per the `wallets.css` 760px rules
- [x] 2.5 Transfer note "A move, not an expense." with "Move money"; Recent transfers list opening the edit modal; archived section and empty state restyled
- [x] 2.6 View tests: rows link to activity, edit/archive URLs present per row, no Transfer money action enabled with one wallet, recent transfers order, archived wallet absent from table and breakdown

## 3. Modals

- [x] 3.1 Add-wallet preview card bound to name and type with Alpine (design decision 7)
- [x] 3.2 `TransferForm` overdraft check counting the edited transfer's own amount (design decision 5); form tests: too much, exactly the balance, edit counts the old amount, other users' wallets still rejected
- [x] 3.3 Transfer modal layout (From | swap | To with available/current balance, large Rp amount box, date, note, summary box) and the `transferForm` Alpine component with balances from `json_script`; submit label "Transfer Rp…"; works without JavaScript
- [x] 3.4 View tests: transfer modal includes the balances JSON, the overdraft message is shown on POST, Transactions page transfer still works

## 4. Wrap-up

- [x] 4.1 Headless screenshots of the Figma Make Wallets screen and of the new page at 1440px and 390px with the demo account, including both modals; fix layout differences
- [x] 4.2 Update the README/STYLE.md page map entry for Wallets (local docs), write `changes.md`, and add the commit record in `openspec/commits/`
- [x] 4.3 Update docs/decisions.md (wallet table instead of cards, transfers can't overdraw, monogram removed) and run `python manage.py test` and `openspec validate redesign-wallets-page --strict`

## Workflow follow-up

- After the developer checks the page in a real browser, run `openspec archive redesign-wallets-page`.
