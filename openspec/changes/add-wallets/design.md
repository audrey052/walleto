# Design

## Context

MVP 0 delivered accounts, the app shell and placeholder pages. The Wallets placeholder is served by `core.views.wallets`. Shared pieces available: CSS component classes, the `{% icon %}` tag, the money helpers, `components/field.html` and a static `<dialog>` modal partial. HTMX 2.0.4 and Alpine 3.14.9 are loaded on every page, and `base.html` already sends the CSRF token as an HTMX header.

## Goals / Non-Goals

**Goals:**
- A data model for wallets and categories that transactions, transfers and budgets can build on without migration pain.
- A Wallets page that matches the Figma design and works without reloads, but also without JavaScript.
- A single way to parse Rupiah amounts, reused by every later form.

**Non-Goals:**
- Balances from transactions (MVP 2).
- Category management UI.

## Decisions

### 1. One `finance` app for all money data
Wallets, categories, and later transactions, transfers, budgets and savings goals live in `finance`. They reference each other constantly (a transaction needs a wallet and a category; a budget needs a category).
- Rejected: one app per feature. Cross-app foreign keys and import cycles for no gain at this size.

### 2. Amounts are `BigIntegerField` holding whole Rupiah
Rupiah has no minor unit in daily use, so an integer is exact and simple. `BigIntegerField` holds up to 9.2 × 10^18.
- Rejected: `DecimalField`. Correct too, but every value would carry a meaningless `.00`, and arithmetic would need `Decimal` everywhere.
- Rejected: `FloatField`. Not exact; forbidden by the project rules.

### 3. Archive, never delete
`Wallet.is_archived` (with `archived_at`) hides a wallet from the cards and the total. There is no delete action. Transactions in MVP 2 will point at wallets with `on_delete=PROTECT`.
- Rejected: hard delete. It would either cascade into transaction history or fail once transactions exist.

### 4. Unique active wallet names enforced by the database
A conditional unique constraint on `(user, Lower(name))` where `is_archived = False`. The form checks first to show a friendly message; the constraint guarantees it.
- Rejected: form-only validation. Two quick submissions could still create duplicates.

### 5. Balance as a queryset annotation
`Wallet.objects.with_balance()` annotates `balance`. Today it is `initial_balance`; MVP 2 changes only this method to add sums of income, expenses and transfers. Templates and the total always read `balance`.
- Rejected: a stored `balance` column. It would have to be kept in sync with every transaction edit.

### 6. Monogram and color are derived or assigned, not chosen
`Wallet.monogram` is a property computed from the name and type (rules in the `wallets` spec). `Wallet.color` is stored and assigned on creation by cycling through a fixed list of muted colors taken from the Figma wallet cards (`#426050`, `#597D73`, `#8D826E`, `#A39C87`, `#1F5C4A`).
- Rejected: a color picker. Extra form complexity, and free colors would break the restrained palette.

### 7. Categories: one table, `user` NULL for defaults
`Category(user nullable, name, kind, color, icon, order)`. Defaults have `user = NULL` and are created by a data migration. `Category.objects.for_user(user)` returns defaults plus the user's own, ordered by kind, order and name. Unique constraints: `(Lower(name), kind)` among defaults, and `(user, Lower(name), kind)` among a user's own.
- Rejected: copying defaults into every new user's rows. More rows, and changing a default later would mean updating every user.

### 8. Shared `AmountField` in `core/forms.py`
A `forms.CharField` subclass that strips an optional "Rp", spaces, dots and commas, and requires the rest to be digits. Returns an `int`. Widget uses `inputmode="numeric"`.
- Rejected: `IntegerField` with `localize`. It rejects "Rp" and mixed separators, and depends on locale settings.

### 9. HTMX modals with a no-JavaScript fallback
Buttons use `hx-get` to load a modal fragment into `#modal-root`. The fragment is a `<dialog>` that opens itself (`x-init="$el.showModal()"`) and removes itself when closed. Its form posts with `hx-post` and swaps the whole dialog on validation errors. On success the view returns an `HX-Redirect` to the Wallets page, which shows the toast through the messages framework. Without HTMX (direct visit, tests), the same views render a full page and redirect normally.
- Rejected: returning only the updated card list. Simpler to reload once than to keep the total, the cards and the archived list in sync with out-of-band swaps; the page is light.

### 10. Active section from a view-name prefix
Sections get a `match` prefix (for Wallets `finance:wallet`), so every wallet view (list, create, edit, archive) marks Wallets active in the sidebar.

## Risks / Trade-offs

- **Editing the starting balance after MVP 2** silently shifts the current balance. Acceptable: it is how users fix a wrong starting value; the edit form will explain it once transactions exist.
- **Full reload after each save** costs one page load. Acceptable for a page of a few cards.
- **Conditional unique constraints** need database support. SQLite and PostgreSQL both support partial unique indexes.
