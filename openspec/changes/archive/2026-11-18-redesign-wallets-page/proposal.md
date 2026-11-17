# Proposal

## Why

The Wallets page was built in MVP 1 as a grid of cards, before the Figma Make design had a dedicated Wallets screen. The design now shows a richer page: the total next to a breakdown by wallet type, a table of wallets with a 30-day balance trend, a note explaining transfers, recent transfers, and a transfer modal that shows what each wallet will hold afterwards. Matching it makes Wallets consistent with the Transactions and Budget pages, and the transfer preview prevents a common mistake: moving more money than the source wallet has.

## What Changes

- **Balance panel in two columns**: the total balance of active wallets with "Across N wallets · As of <today>" on the left, and totals for Bank accounts, E-wallets and Cash on the right.
- **"Your wallets" table instead of cards**: columns Wallet, Type, Last 30 days (a small balance trend line), Balance, and a chevron. The heading shows the wallet count and the 30-day date range. Clicking a row opens the Transactions page filtered to that wallet.
- **Edit and archive move to the row**: icons appear when the row is hovered or focused, and are always visible on phones.
- **Table footer**: "Add another wallet" and "All balances in Indonesian Rupiah".
- **Transfer note**: "A move, not an expense." with a short explanation and a "Move money" action.
- **Recent transfers**: the three most recent transfers, each opening its edit modal.
- **Heading actions**: "Add wallet" (secondary) and "Transfer money" (primary, disabled with fewer than two active wallets).
- **Add-wallet modal**: a live preview card showing the name and type as they are typed.
- **Transfer modal**: the available balance under From, the current balance under To, a button to swap them, a large amount input with an "Rp" prefix, and a summary of both balances after the transfer, with "Your total balance stays the same." The submit button names the amount.
- **BREAKING (behavior)**: a transfer can no longer be larger than the source wallet's current balance. The form says "Not enough in <wallet>. Choose another wallet or a smaller amount." Expenses can still make a balance negative.
- **Wallet monograms are removed**: the table shows the wallet name only, as in the design.
- The archived-wallets section and the empty state stay, restyled to match.
- Copy follows docs/STYLE.md: no poetic overlines or notes. The subtitle stays "Balances across your cash, bank and e-wallets."

Out of scope:
- Connecting real bank accounts or showing account numbers.
- Changing how balances are computed.
- Applying the new layout to other pages, the sidebar or the topbar.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `wallets`: the page layout (panel, table, breakdown, 30-day trend, recent transfers, row actions), the wording of scenarios that referred to cards, and removal of the monogram requirement.
- `transfers`: a transfer can't exceed the source wallet's balance, and the form previews balances after the transfer.

## Impact

- `finance/views.py`: wallet list context (breakdown, 30-day history, recent transfers).
- New `finance/history.py` (or a function in `finance/budgets.py`'s style): daily balances for the last 30 days, computed in two queries.
- `finance/forms.py`: `TransferForm` balance check (edit-aware).
- `finance/views_activity.py`: transfer modal context (wallet balances for the live preview).
- Templates: `finance/wallets.html` rewritten; `_wallet_fields.html` (preview card); `_transfer_fields.html` (new layout with Alpine.js for the live summary).
- `finance/models.py`: `Wallet.monogram` removed.
- Tests for the history, the breakdown, the overdraft rule and the page.
- No new dependencies, no migration.
