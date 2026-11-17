# Design

## Context

The Wallets page (`finance/views.py:wallet_list`, `templates/finance/wallets.html`) shows the total balance and a grid of cards with a monogram, the balance, "View activity", edit and archive. Balances come from `WalletQuerySet.with_balance()` (four correlated subqueries). Transfers use `TransferForm` and `templates/finance/_transfer_fields.html` inside the shared modal (`components/modal_form.html`); the same modal is opened from the Wallets and Transactions pages. Alpine.js components live in `static/js/app.js`.

The target is the Figma Make Wallets screen (`SqCtFlkW2pwTXgwnAeHSdb`, `src/WalletsPage.tsx`, `src/wallets.css`). The developer chose: STYLE.md copy (no poetic overlines or notes), edit and archive as row icons on hover, block transfers larger than the source balance, and a separate OpenSpec change. Text sizes follow the docs/STYLE.md scale, as on the other pages; layout, spacing, colors and structure follow `wallets.css`.

## Goals / Non-Goals

**Goals:**
- A Wallets page whose layout and design match the Figma screen, at desktop and phone widths.
- A 30-day trend per wallet that is computed by code and costs a fixed number of queries.
- A transfer form that previews the result and refuses to overdraw.

**Non-Goals:**
- Restyling the app shell, Transactions or Budget.
- Changing the balance formula or allowing negative balances to be prevented for expenses.

## Decisions

### 1. Table rows as links, actions as separate buttons
Each row is a CSS grid (`1.6fr 1fr 1fr 1.2fr auto`, as in `.account-row`) whose main area is an `<a>` to `finance:transactions?wallet=<id>`. The edit and archive icons are separate `<a>` elements with `hx-get` into `#modal-root`, positioned in the last column, so choosing them never follows the row link. They use `opacity-0 group-hover:opacity-100 group-focus-within:opacity-100`, and `opacity-100` below `md`.
- Rejected: making the whole row a `<button>` like Figma. Nested interactive elements inside a button are invalid HTML and break keyboard use.
- Rejected: a "…" menu. It adds a popover for two actions.

### 2. 30-day history in Python from two queries
New `finance/history.py`, `balance_history(wallets, today, days=30)`:
1. Current balances come from `with_balance()` (already loaded for the page).
2. One query each for transactions and transfers of these wallets dated after `today - 30 days`, as `(wallet_id, date, signed amount)`.
3. Walk backwards from today: `balance[day-1] = balance[day] - movements on day`. Movements dated in the future are not possible (forms refuse them).

The result is `{wallet_id: [30 ints]}`, oldest first.
- Rejected: 30 `with_balance()` calls with a date filter. That is 30 × 4 subqueries.
- Rejected: storing daily snapshots. They would drift when a past transaction is edited, the same reason balances are not stored.

### 3. Sparkline as server-rendered inline SVG
A template tag `{% sparkline values %}` returns a 120×32 SVG path, scaled between the 30-day min and max, with a baseline and an end dot, matching `Sparkline` in `WalletsPage.tsx`. A flat series draws a horizontal line at mid-height. The color is `forest` at 65% opacity.
- Rejected: ApexCharts for each row. It needs JavaScript and is heavy for five tiny lines; the page should render fully without JavaScript.

### 4. Breakdown and recent transfers in the view
`wallet_list` adds `breakdown` (three sums by `Wallet.Type` over the active wallets already annotated with balances), `history`, `date_range` (first and last day), and `recent_transfers` (`Transfer.objects.for_user(user).select_related(...)[:3]`, ordered by the model's default `-date, -created_at`).

### 5. Overdraft check in `TransferForm.clean()`
`available = source balance (with_balance) + (instance.amount if editing and instance.from_wallet == source else 0)`. If `amount > available`, add the error to `amount`: "Not enough in <name>. Choose another wallet or a smaller amount." The check runs only when the other fields are valid.
- Rejected: a database constraint. A balance is computed across tables; a check constraint cannot express it.
- Rejected: client-side only. The server must enforce the rule (project rule: numbers are computed and validated by code).

### 6. Transfer preview with Alpine.js, server-rendered fallback
The view passes `{wallet_id: balance}` for the selectable wallets (plus the edited transfer's adjustment) as JSON via `json_script`. An Alpine component `transferForm` reads it, watches From, To and Amount (parsing the same separators as `AmountField`), and shows the available/current balances, the after-transfer summary, the insufficient message and the "Transfer Rp…" label. It disables submit when the amount is too large. Without JavaScript the plain fields work and the server validates.
- Layout from Figma: From | swap button | To in a three-column grid, the amount in a 57px-high box with "Rp" prefix and large forest digits, then date and note, then the summary box.
- The date field stays (transfers spec requires a date); Figma has none.

### 7. Add-wallet preview card
`_wallet_fields.html` gets a preview card at the top bound with Alpine `x-text` to the name and type fields ("Your new wallet" when empty). The Figma "YOURS TO NAME" label is dropped (STYLE.md copy rules).

### 8. Copy kept or dropped
Kept (informative): "Across N wallets · As of <date>", "Your wallets", the date range, "Add another wallet", "All balances in Indonesian Rupiah", "A move, not an expense." with "Transfers keep your balances in sync without changing your total or your budget.", "Recent transfers", "Your total balance stays the same.". Dropped (poetic, per STYLE.md section 6): the page overline, "Your money, wherever you keep it.", "Every Rupiah, accounted for.", "A little structure. A clearer view.", "Different purposes. All in one place.", "A clear trail, between your wallets.", and the sample-data note.

### 9. Remove `Wallet.monogram`
The property and its tests go; `WALLET_COLORS` and `Wallet.color` stay (Transactions uses the color dot).

## Risks / Trade-offs

- [Existing transfers may already exceed what was available] → The rule applies when saving; old transfers stay. Editing one re-checks it, counting its own amount.
- [Overdraft check uses the balance over all dates, not the balance on the transfer's date] → Simple and matches what the page shows; a backdated transfer could still be blocked by later spending. Acceptable for a personal app.
- [Hover-only icons are invisible on touch devices] → Always visible below 768px, and visible on keyboard focus.
