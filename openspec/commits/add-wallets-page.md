# Wallets Page with Add, Edit, Archive and Restore

**Created:** 2026-11-16
**Last edited:** 2026-11-16
**Status:** Implemented
**Commit:** `605f480` feat: add wallets page with add, edit, archive and restore
**Branch:** `main`, parent `44b0090`
**OpenSpec change:** `add-wallets` (MVP 1), tasks 2.1–2.2, 3.1–3.4, 4.1–4.6, 5.3–5.5
**Trigger:** spec `wallets`; the Wallets section was still the MVP 0 placeholder.

## Why this is recorded here

- **New routes** under `/wallets/`, the first ones that change user data.
- **Two shared building blocks** that later forms reuse: `AmountField` for Rupiah input and the HTMX form/modal helpers.
- **A change to the app shell:** sections can now span several views through a `match` prefix.

## Context

- **Modals load over HTMX and fall back to full pages.** The same view returns a `<dialog>` fragment for HTMX requests and a full page otherwise. On success it answers `204` with `HX-Redirect` (or a normal `302`), so the page reloads once and the toast comes through Django's messages framework. Design decision 9.
- **Privacy by lookup.** Every wallet view fetches with `get_object_or_404(Wallet, pk=pk, user=request.user)`, so another user's wallet is a 404, not a 403. That doesn't reveal that the wallet exists.
- **Archive asks first; restore doesn't.** Archiving is confirmed in a modal. Restoring is a single POST button, since it's undone just as easily. GET on restore returns 405.
- **The form sets `instance.user` before validation,** so the model's unique and check constraints are validated by the form too, not only by the database.

## What is built

### Routes (`finance/urls.py`)

| Method | URL | Name | Purpose |
|---|---|---|---|
| GET | `/wallets/` | `finance:wallets` | Total balance, wallet cards, archived list, empty state |
| GET/POST | `/wallets/new/` | `finance:wallet_create` | Add wallet; toast "Wallet added." |
| GET/POST | `/wallets/<id>/edit/` | `finance:wallet_edit` | Edit name, type, starting balance; toast "Wallet updated." |
| GET/POST | `/wallets/<id>/archive/` | `finance:wallet_archive` | GET: confirmation; POST: archive, toast "{name} archived." |
| POST | `/wallets/<id>/restore/` | `finance:wallet_restore` | Restore, toast "{name} restored."; error toast if an active wallet has the same name |

All require sign-in (global middleware). The `core` Wallets placeholder view and URL were removed.

### `AmountField` (`core/forms.py`)

| Input | Result |
|---|---|
| `2.500.000`, `Rp 1,250,000`, `Rp2.500.000`, `rp. 750.000`, `1 250 000`, `2500000` | integer |
| empty (not required) | 0 |
| `dua juta`, `2,5`, `2.5jt`, `1.25.000`, `Rp` | "Enter an amount in Rupiah, for example 2.500.000." |
| `-50.000` | "Amount cannot be negative." unless `allow_negative=True` |
| ≥ 10^15 | "That amount is too large." |

Separators must group digits in threes. Re-displayed values use dot separators. Widget: `inputmode="numeric"`.

### `WalletForm` (`finance/forms.py`)

Fields `name`, `type`, `initial_balance` (as `AmountField`, optional). The name is trimmed and inner spaces collapsed. "Enter a name for this wallet." when empty; "You already have a wallet with this name." when an active wallet of the same user matches ignoring case, excluding the wallet being edited.

### HTMX helpers (`core/htmx.py`)

`is_htmx(request)`, `render_form(request, context)` (picks `components/modal_form.html` or `components/form_page.html`), `redirect_after_save(request, url)`.

### Templates

| Template | Job |
|---|---|
| `components/modal_form.html` | `<dialog>` that opens itself, focuses the first invalid field (or the first field), closes on Cancel, ✕, Escape or a backdrop click, removes itself on close; the form posts over HTMX and swaps the whole dialog |
| `components/form_page.html` | Same form as a full page, with a Cancel link |
| `finance/wallets.html` | Heading with "Add wallet"; total balance block ("Across N active wallets"); two-column card grid (monogram tile in the wallet's color, name, type, balance, "Added …", Edit and Archive); collapsible "Archived wallets (N)" list with Restore; empty state "Add your first wallet"; `#modal-root` |
| `finance/_wallet_fields.html` | Non-field errors and the three fields |
| `finance/_wallet_archive_body.html` | What archiving does and that it can be undone |

### App shell

- `core/sections.py`: Wallets points at `finance:wallets` with `match: "finance:wallet"`.
- `core/context_processors.py`: a section is active when the view name equals its URL name or starts with its `match` prefix.

## Requirements this establishes

1. **Every view that loads a user-owned object filters by `user=request.user`** and answers 404 otherwise.
2. **Every money input uses `AmountField`.**
3. **Data-changing actions are POST-only.** GET at most shows a confirmation.
4. **Forms work with and without HTMX.**

## Files changed

| File | Change |
|---|---|
| `core/forms.py` | new: `AmountField` |
| `core/htmx.py` | new: form and redirect helpers |
| `core/test_forms.py` | new: 10 tests |
| `core/sections.py`, `core/context_processors.py` | Wallets section moved to `finance`, `match` prefix |
| `core/views.py`, `core/urls.py` | Wallets placeholder removed |
| `config/urls.py` | includes `finance.urls` |
| `finance/forms.py`, `finance/views.py`, `finance/urls.py` | new |
| `finance/tests/test_views.py` | new: 30 tests |
| `accounts/tests.py`, `core/tests.py` | `core:wallets` → `finance:wallets` |
| `templates/components/modal_form.html`, `templates/components/form_page.html` | new |
| `templates/finance/wallets.html`, `_wallet_fields.html`, `_wallet_archive_body.html` | new |
| `openspec/commits/README.md` | index: `44b0090` filled in, this record added |
| `openspec/commits/add-wallet-and-category-models.md` | its own hash filled in |

## Verification

**Executed:**

- **90 tests pass** (whole suite). The wallet view tests cover:
  - list: empty state, total and order of active wallets, archived count, only own wallets, cash monogram, Wallets active on all four wallet pages, visitors redirected
  - create: HTMX fragment vs full page, HTMX `HX-Redirect` with toast, plain redirect, empty balance = 0, blank name keeps the modal with entered values, duplicate in any case, archived name reusable, negative and non-numeric balance, owner can't be injected through POST data
  - edit: rename with toast, same name in another case allowed for itself, clash with another active wallet, current values pre-filled with dot separators
  - archive/restore: GET only confirms, archive removes from cards and total, restore with toast, restore blocked by an active name, GET on restore is 405
  - privacy: edit, archive and restore of another user's wallet return 404 and change nothing
- **Headless Edge screenshots:** wallets page with four active and one archived wallet at 1440px and 390px; add-wallet modal with two errors at 1440px; empty state.

**Fixed during implementation:**

- `AmountField` first kept `CharField`'s `max_length`, whose validator ran on the integer result (`TypeError: object of type 'int' has no len()`). The length check moved into `to_python`.
- A name of only spaces got Django's generic "This field is required."; the form now says "Enter a name for this wallet."
- The modal focused its ✕ button, because the focus selector matched the hidden CSRF input first. It now focuses the first invalid field, or the first visible field.

**Not executed:**

- A real-browser pass of the modal flow (open, error, save, toast) and the archived list toggle.

## Known gaps

- **Balances equal the starting balance** until MVP 2 adds transactions.
- **Each save reloads the page** instead of swapping only the changed card; an accepted trade-off (design decision 9).
- **No "View activity" link** on cards yet; it needs the transactions list (MVP 2).
