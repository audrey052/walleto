# Changes: redesign-wallets-page

Implementation log for this change: what was created or modified, and where the result differs from `proposal.md`, `design.md` and `tasks.md`. Per-commit detail is in `openspec/commits/`.

- **Status:** implemented, archived 2026-11-18
- **Date:** 2026-11-17
- **Tests:** 235 passing in about 6 s; 22 new in `finance/tests/test_wallets_page.py`
- **Validation:** `openspec validate redesign-wallets-page --strict` passes; `makemigrations --check` finds no changes

## Commits

| Commit | Message | Record |
|---|---|---|
| `e3e407f` | feat: redesign the wallets page after the figma table and block overdrawn transfers | `redesign-wallets-page.md` |

## Routes

No new routes. `finance:wallets` gets a new layout and context; `finance:transfer_create` and `finance:transfer_edit` get the preview data and the overdraft check.

## Files

### Backend
- `finance/history.py` (new): `balance_history(wallets, today, days=30)`, current balances walked backwards with two queries.
- `finance/views.py`: `wallet_list` adds `breakdown`, per-wallet `history`, `history_start`, `recent_transfers`, `can_transfer`.
- `finance/forms.py`: `TransferForm` overdraft check (`NOT_ENOUGH`), first two active wallets as defaults for a new transfer, large amount input classes.
- `finance/views_activity.py`: `_transfer_wallets` (balances for the preview, before the edited transfer) and the Alpine hooks in the modal context.
- `finance/models.py`: `Wallet.monogram` removed.
- `core/templatetags/charts.py` (new): `{% sparkline %}`.

### Frontend
- `templates/finance/wallets.html`: rewritten after `WalletsPage.tsx` / `wallets.css`: heading actions, two-column balance panel, "Your wallets" table with trend lines and hover actions, footer, transfer note, recent transfers, restyled archived list.
- `templates/finance/_transfer_fields.html`: From | swap | To with balances, large Rp amount box, date and note, after-transfer summary.
- `templates/finance/_wallet_fields.html`: live preview card.
- `templates/components/modal_form.html`, `form_page.html`: optional `form_x_data`, `submit_x_text`, `submit_x_disabled`.
- `static/js/app.js`: `walletPreview` and `transferForm` Alpine components.

### Tests
- `finance/tests/test_wallets_page.py` (new): history (expense, transfer, flat, before the window, fixed query count), sparkline geometry, breakdown, rows and actions, archived wallet, disabled Transfer money, recent transfers, overdraft (too much, exact, edit, other users), transfer modal JSON and labels.
- `finance/tests/test_models.py`, `test_views.py`, `test_activity.py`: monogram tests removed, card wording updated.

### Documentation (local only: these files are in `.gitignore`)
- `docs/STYLE.md`: Wallets row of the page map.
- `docs/decisions.md`: three decisions.

## Differences from the plan

- **Row actions sit in the "Last 30 days" cell on desktop.** Design decision 1 planned them in the last column; that pushed the Balance column left of where Figma has it. They now appear after the trend line on hover or focus, and the last column is Figma's 24px chevron. On phones they stay in the last column, always visible.
- **New transfers start with the first two active wallets selected,** as the Figma modal starts with BCA → GoPay, so the balances and summary show immediately. Not in the tasks; it only sets initial values.
- **Cash keeps the label "Cash"** (Figma: "Cash wallet"), since changing the choice label would need a migration and is not in the spec.

## Verification

- `python manage.py test`: 235 tests OK.
- The Figma Make source was built locally and screenshotted (Wallets page, transfer modal, add-wallet modal) at 1440px, and compared with the new page at 1440px and 390px using the demo account. Layout, columns, panel, note and modals match; remaining differences are the copy rules from docs/STYLE.md, the date field in the transfer modal, and the app shell.

## Open items before archiving

None. Archived at the developer's request; the real-browser pass was left to the developer.
