# Transfers Start from Wallets Only

**Created:** 2026-11-24
**Last edited:** 2026-11-24
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `d4284f7`
**OpenSpec change:** none (page layout; no spec requires the button)
**Trigger:** The developer asked to remove the Transfer button from Transactions and keep transfers on Wallets.

## Why this is recorded here

There is now one place to start a transfer.

## Context

- Transactions had a "Transfer" button next to "Add transaction" when the user had two or more active wallets. Wallets has "Transfer money" with the same modal.

## What is built

| Area | Change |
|---|---|
| Transactions heading | month picker and "Add transaction" only |
| Transfer rows on Transactions | unchanged: still listed, filtered by wallet, and open the transfer edit modal |

## Requirements this establishes

1. **A new transfer starts from Wallets.** Transactions does not link to `finance:transfer_create`.

## Files changed

| File | Change |
|---|---|
| `templates/finance/transactions.html` | Transfer button removed |
| `finance/views_activity.py` | unused `can_transfer` removed from the Transactions context |
| `finance/tests/test_activity.py` | the page has no new-transfer link |
| `openspec/commits/README.md`, `smiling-wallet-logo.md` | `d4284f7` filled in, this record |

## Verification

**Executed:**

- `python manage.py test`: 353 tests OK.

**Not executed:**

- No browser check; the change removes one link.

## Known gaps

- None.
