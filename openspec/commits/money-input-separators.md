# Add Dot Separators to Money Inputs While Typing

**Created:** 2026-11-23
**Last edited:** 2026-11-23
**Status:** Implemented
**Commit:** `5cec7fa` feat: add dot separators to money inputs while typing
**Branch:** `main`, parent `c699a64`
**OpenSpec change:** none (input behavior across existing forms; the money-format spec already accepts "2.000.000")
**Trigger:** The developer asked for amounts to show dots as they are typed (2000000 → 2.000.000), so they are easier to read.

## Why this is recorded here

Every money field in the app changes how it behaves while typing. The fields are wallet starting balance, transaction, transfer, budget plan and limit, goal target, and goal deposits and withdrawals.

## Context

- `AmountField` already parsed "2.000.000" and re-displayed saved values with dots. Only typing showed bare digits.

## What is built

| Area | Change |
|---|---|
| `core/forms.py` | `AmountField` widgets get `data-money` (not for fields that allow negative amounts) |
| `static/js/app.js` | one capture-phase `input` listener formats `data-money` inputs: keeps digits only, drops leading zeros, groups by three with dots, at most 15 digits, and keeps the caret after the same digit |

Without JavaScript the field keeps working: the server accepts both "2000000" and "2.000.000".

## Requirements this establishes

1. **Money inputs show dot separators while typing.** The capture-phase listener runs before Alpine's form listeners, so the transfer preview reads the formatted value.

## Files changed

| File | Change |
|---|---|
| `core/forms.py`, `core/test_forms.py` | `data-money` attribute and test |
| `static/js/app.js` | the formatter |
| `openspec/commits/README.md`, `placeholders-without-eg.md` | `c699a64` filled in, this record |

## Verification

**Executed:**

- `python manage.py test`: 311 tests OK (1 new).
- Edge over the DevTools protocol, demo account:
  - typing 2000000 into a new wallet's starting balance showed 2 → 20 → 200 → 2.000 → 20.000 → 200.000 → 2.000.000;
  - inserting 5 after the first digit gave 25.000.000 with the caret after the 5;
  - saving showed the wallet at Rp25.000.000;
  - in the transfer modal, 200000 became 200.000 and the button read "Transfer Rp200.000".
- The demo data was reset with `seed_demo` afterwards.

**Not executed:**

- None.

## Known gaps

- **Typing a decimal such as "2,5" now becomes 25** instead of an error, because the comma is dropped as it is typed. Rupiah has no decimals, so this is unlikely in practice.
