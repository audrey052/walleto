# Redesign the Wallets Page After the Figma Table and Block Overdrawn Transfers

**Created:** 2026-11-17
**Last edited:** 2026-11-17
**Status:** Implemented, with the real-browser check outstanding
**Commit:** this commit
**Branch:** `main`, parent `bb06f5c`
**OpenSpec change:** `redesign-wallets-page`, proposal and tasks 1.1–4.3
**Trigger:** Developer request to make the Wallets page match the Figma Make Wallets screen (`SqCtFlkW2pwTXgwnAeHSdb`, `WalletsPage.tsx`, `wallets.css`), with STYLE.md copy, hover row actions, and transfers blocked above the source balance.

## Why this is recorded here

A new behavior rule (a transfer can't overdraw its source), a new history computation, a new template tag, the removal of `Wallet.monogram`, and new optional hooks in the shared modal templates.

## Context

- MVP 1 built Wallets as a grid of cards before the design had a Wallets screen.
- Departures from `design.md` are in `openspec/changes/redesign-wallets-page/changes.md`: row actions in the trend cell on desktop, default wallets in a new transfer, "Cash" label kept.

## What is built

### Modules

| Module | Job |
|---|---|
| `finance/history.py` | 30 end-of-day balances per wallet from current balances and two queries |
| `core/templatetags/charts.py` | `{% sparkline %}` inline SVG (Figma geometry) |
| `static/js/app.js` | `walletPreview` and `transferForm` Alpine components |

### Behavior

| Area | Rule |
|---|---|
| Wallets page | balance panel with breakdown by type, table with trend, footer, transfer note, three recent transfers |
| Transfers | amount ≤ source balance; an edit counts its own amount; message "Not enough in <wallet>. Choose another wallet or a smaller amount." |

## Requirements this establishes

1. **Transfers can't overdraw their source wallet;** expenses still can make a balance negative.
2. **The 30-day trend costs two queries** regardless of the number of wallets.
3. **Live previews are optional:** every form works without JavaScript and the server validates.

## Files changed

| File | Change |
|---|---|
| `finance/history.py`, `core/templatetags/charts.py`, `finance/tests/test_wallets_page.py` | new |
| `finance/views.py`, `finance/views_activity.py`, `finance/forms.py`, `finance/models.py`, `finance/demo.py` | page context, transfer preview data, overdraft check, monogram removed |
| `templates/finance/wallets.html`, `_transfer_fields.html`, `_wallet_fields.html` | new layout |
| `templates/components/modal_form.html`, `form_page.html`, `static/js/app.js` | Alpine hooks and components |
| `finance/tests/test_models.py`, `test_views.py`, `test_activity.py` | monogram tests removed, wording updated |
| `openspec/changes/redesign-wallets-page/` | proposal, specs, design, tasks, changes |
| `openspec/changes/add-budgets/changes.md`, `openspec/commits/add-budgets.md`, `openspec/commits/README.md` | `bb06f5c` filled in, this record added |

## Verification

**Executed:**

- `python manage.py test`: 235 tests OK (22 new).
- `makemigrations --check`: no changes. `openspec validate redesign-wallets-page --strict`: valid.
- Headless Edge: a local build of the Figma Make source (Wallets page, both modals) compared with the new page at 1440px and 390px with the demo account.

**Fixed during implementation:**

- The 76px actions column moved the Balance column left of Figma's; the actions moved into the trend cell.
- The transfer modal opened with no wallets selected, hiding the balances; new transfers now default to the first two active wallets.

**Not executed:**

- Real-browser check of hover, swap and the live summary.

## Known gaps

- **Real-browser check is open** before archiving.
- **`docs/STYLE.md` and `docs/decisions.md` updates are local only** (`.gitignore`).
