# Tasks

## 1. Finance app and models

- [x] 1.1 Create the `finance` app and add it to `INSTALLED_APPS`
- [x] 1.2 `Wallet` model: `user`, `name`, `type` (cash, bank, ewallet), `initial_balance` (`BigIntegerField`, ≥ 0), `color`, `is_archived`, `archived_at`, `created_at`, `updated_at`; conditional unique constraint on active `(user, Lower(name))`; check constraint `initial_balance >= 0`
- [x] 1.3 `Wallet.monogram` property and color assignment on creation, following the `wallets` spec and `design.md` decision 6
- [x] 1.4 `WalletQuerySet`: `active()`, `archived()`, `with_balance()`, `for_user(user)`
- [x] 1.5 `Category` model: `user` (nullable), `name`, `kind` (expense, income), `color`, `icon`, `order`; unique constraints for defaults and per user; `CategoryQuerySet.for_user(user)`
- [x] 1.6 Data migration creating the nine default categories with colors from the chart palette and icons
- [x] 1.7 Add the icons the default categories need (`heart`, `ticket`, `briefcase`, `gift`) and the wallet actions need (`archive`, `edit`, `restore`) to the `{% icon %}` set
- [x] 1.8 Register `Wallet` and `Category` in the admin

## 2. Amount input

- [x] 2.1 `AmountField` in `core/forms.py`: optional "Rp", dots, commas and spaces; whole numbers only; empty means 0 when not required; clear error message
- [x] 2.2 Unit tests for every scenario in the `Rupiah amount input` requirement

## 3. Wallets page

- [x] 3.1 Move the Wallets section from `core` to `finance:wallets`; sections get a `match` prefix so every wallet view marks Wallets active
- [x] 3.2 Wallet list view: total of active wallets (database aggregate), cards in creation order, archived list, empty state
- [x] 3.3 Templates: page heading with "Add wallet", total block, card grid (monogram tile, name, type, balance, footer actions), archived section (collapsible), empty state
- [x] 3.4 `WalletForm` (name, type, starting balance) with the case-insensitive duplicate check against active wallets

## 4. Add, edit, archive, restore

- [x] 4.1 Reusable HTMX modal partial: `<dialog>` that opens itself, closes on Cancel, ✕, Escape or backdrop click, and removes itself from the page
- [x] 4.2 Create view: modal fragment for HTMX, full page otherwise; on success `HX-Redirect` (or normal redirect) and "Wallet added." toast
- [x] 4.3 Edit view with the same behavior and "Wallet updated." toast
- [x] 4.4 Archive: confirmation modal, POST-only action, "{name} archived." toast
- [x] 4.5 Restore: POST-only action from the archived list; error toast when an active wallet has the same name
- [x] 4.6 Every wallet lookup uses `get_object_or_404(Wallet, pk=..., user=request.user)`

## 5. Tests

- [x] 5.1 Model tests: monogram rules, color assignment, active-name constraint, check constraint, `with_balance()`
- [x] 5.2 Category tests: nine defaults with kinds and order, `for_user` excludes other users' categories, unique name per user and kind
- [x] 5.3 View tests: list shows only own wallets, total of active wallets, empty state, create (HTMX and plain), validation errors keep the modal, duplicate name, edit, archive hides from list and total, restore, restore blocked by name in use, archived name reusable
- [x] 5.4 Privacy tests: edit, archive and restore of another user's wallet return 404 and change nothing; GET on archive and restore actions does not change anything
- [x] 5.5 Update MVP 0 tests that referenced `core:wallets`

## 6. Wrap-up

- [ ] 6.1 Check the Wallets page at 1440px and 390px against docs/STYLE.md and the Figma design (headless screenshots done; developer to do a real-browser pass)
- [x] 6.2 Write `changes.md` and a record per commit in `openspec/commits/`
- [x] 6.3 Update docs/decisions.md
- [x] 6.4 Run `openspec validate add-wallets --strict`
