# Simplify Wallets and Transactions

**Created:** 2026-11-24
**Last edited:** 2026-11-24
**Status:** Implemented
**Commit:** `7b04a3a` fix: simplify wallets and transactions
**Branch:** `main`, parent `89bd29e`
**OpenSpec change:** none for the main wallets spec (edited directly); the active `add-savings-goals` delta was updated so archiving it doesn't bring removed parts back
**Trigger:** A series of developer requests to remove duplicated or unneeded parts of the Wallets and Transactions pages.

## Why this is recorded here

Several sections of the Wallets page are removed, along with a module and a template tag. Two requirements of the main wallets spec change.

## Context

- Most of the removed parts came from redesign-wallets-page (Figma `WalletsPage.tsx`).
- Squashed from two unpushed commits: "remove duplicate buttons" and "simplify wallets page".

## What is built

| Area | Change |
|---|---|
| Wallets heading | only "Transfer money"; "Add wallet" removed (the table footer has "Add another wallet", the empty state its own "Add wallet") |
| Wallets table | a `<table>` the same size as Transactions (header, `py-3` rows, 32px icon tile, sideways scroll under 520px): Wallet, Type, Balance, and an always-visible edit icon; a row click opens the wallet's activity |
| Wallets sections removed | the transfer note ("A move, not an expense." / "Move money"), "All balances in Indonesian Rupiah", the "Last 30 days" column with its date range, and Recent transfers |
| Archive | moved from the row into the edit modal as "Archive wallet", which swaps in the existing confirmation |
| Code removed | `finance/history.py`, `core/templatetags/charts.py` (only the trend used them) |
| Transactions | the heading's "Add transaction" is hidden while the empty state shows its own (no entries, no filters, at least one wallet) |

## Requirements this establishes

1. **Each action appears once per page:** one transfer, one add-wallet and one add-transaction entry point.
2. **Wallet rows show name, type and balance,** end with an edit icon, and archiving is in the edit modal.
3. **Wallets doesn't list transfers;** the Transactions page does.

## Files changed

| File | Change |
|---|---|
| `templates/finance/wallets.html`, `templates/finance/transactions.html` | layout |
| `finance/views.py` | no history or recent transfers; archive link in the edit modal |
| `finance/history.py`, `core/templatetags/charts.py` | deleted |
| `finance/tests/test_wallets_page.py`, `test_activity.py`, `test_goals.py` | one entry point each, no trend, archive only in the modal, no Recent transfers |
| `openspec/specs/wallets/spec.md` | "30-day balance trend" and "Recent transfers on Wallets" removed; "Wallet row actions" rewritten; the transfer note sentence removed |
| `openspec/changes/add-savings-goals/specs/wallets/spec.md`, `design.md`, `changes.md` | no trend in the delta; notes |
| `openspec/commits/README.md`, `versioned-static-assets.md` | `89bd29e` filled in, this record |

## Verification

**Executed:**

- `python manage.py test`: all tests OK.
- `openspec validate wallets --type spec` and `openspec validate add-savings-goals --strict`: valid.
- Edge with the demo account:
  - the header is 39px and single-line rows are 57px, as on Transactions;
  - the edit icon opens "Edit wallet" without leaving the page;
  - "Archive wallet" shows "Archive BCA?";
  - a row click opens `/transactions/?wallet=…`.

**Not executed:**

- None.

## Known gaps

- **`docs/STYLE.md` page map updated locally only** (`.gitignore`).
