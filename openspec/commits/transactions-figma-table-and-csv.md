# Match the Transactions Page to the Figma Table and Add CSV Export

**Created:** 2026-11-17
**Last edited:** 2026-11-17
**Status:** Implemented
**Commit:** `90c528b` feat: match the transactions page to the figma table and add csv export
**Branch:** `main`, parent `05a739d`
**OpenSpec change:** `add-transactions` (MVP 2), tasks 3.5, 3.7–3.9
**Trigger:** the developer asked for the Transactions UI to look like the Figma Make design, keeping the font sizes already used in the app.

## Why this is recorded here

- **Spec behavior changed:** daily subtotals were removed and three requirements were split out (one month at a time, summary line, table); CSV export was added.
- **A new route** that returns user data as a downloadable file, with a security measure against CSV formula injection.

## Context

| Part | Before | After (Figma) |
|---|---|---|
| List | grouped by day with signed subtotals | flat table: Transaction, Category, Wallet, **Date**, Amount |
| Summary | three large figures (Income, Expenses, Net) | one line: "N transactions in November 2026" · Monthly income · Monthly expenses · Net |
| Month | arrows and a title above the panel | bordered month picker with a calendar icon in the page heading, next to the actions |
| Toolbar | search, wallet, category | search, wallet, category, **Export CSV** |
| Row icon | tinted with the category color | neutral tile; income uses the arrow-down icon, transfers the transfer icon |
| Wallet cell | name | small square in the wallet's color + name |
| Phone | compact list | the table scrolls sideways (min 680px), as in Figma |

- **Fonts stay on the STYLE.md scale** (control 13, caption 12, body 14), not the 8–11px sizes in the Figma CSS.
- **Net stays in the summary line,** although the Figma line shows only monthly expenses, because the `transactions` spec requires income, expenses and net.
- **The Transfer button stays** next to Add transaction; it isn't in the Figma heading, but transfers need an entry point.
- **One helper (`_activity`) builds the month, filters and merged entries** for both the page and the export, so the file always matches what the page shows.
- **CSV formula injection:** a description such as `=HYPERLINK("http://…")` would run as a formula when the file is opened in Excel. Text cells starting with `=`, `+`, `-`, `@`, tab or carriage return get a leading apostrophe.
- **Rows open the edit modal** from the whole row (`hx-get` on `<tr>`). The link in the first cell is the no-JavaScript fallback and cancels its own navigation when JavaScript runs, so a click doesn't send two requests.
- **The Export link stays in sync** with filters changed through HTMX: a small Alpine `x-init` inside `#results` updates its `href` after each swap.

## What is built

### Route

| Method | URL | Name | Purpose |
|---|---|---|---|
| GET | `/transactions/export/` | `finance:transactions_export` | Same query parameters as the page; returns `walleto-transactions-YYYY-MM.csv` (UTF-8 with BOM) with Date, Type, Description, Note, Category, Wallet, Amount; expenses negative, income positive, transfers "From → To" with an unsigned amount |

### Spec deltas (`openspec/changes/add-transactions/specs/`)

- `transactions`: "Monthly transactions page" split into **One month at a time**, **Month summary line** and **Transactions table** (with a phone-width scenario); "Pagination" now says the summary covers the whole month; new **Export to CSV**, **CSV amounts and transfers**, **Safe CSV text**; the no-results wording follows Figma ("No transactions here yet.").
- `transfers`: transfers appear as a table row with "Transfer" in the Category column; daily subtotals removed.

Proposal, design (decision 4 updated, new decision 6b), tasks (3.8, 3.9) and `changes.md` were updated to match.

## Requirements this establishes

1. **The CSV export always contains exactly the entries the page shows for the same month and filters,** across all pages.
2. **User text in a CSV is never written so that a spreadsheet would run it as a formula.**

## Files changed

| File | Change |
|---|---|
| `finance/views_activity.py` | `_activity` helper; `transaction_list` without day groups; `transaction_export`; `_csv_text`; `transactions_url(view=...)` |
| `finance/urls.py` | `transactions/export/` |
| `templates/finance/transactions.html` | rewritten to the Figma layout |
| `finance/tests/test_activity.py` | day-group tests replaced by table tests; 5 export tests |
| `openspec/changes/add-transactions/specs/transactions/spec.md`, `specs/transfers/spec.md` | as above |
| `openspec/changes/add-transactions/proposal.md`, `design.md`, `tasks.md`, `changes.md` | as above |
| `openspec/commits/README.md` | index: `05a739d` filled in, this record added |
| `openspec/commits/add-transactions-wrap-up.md` | its own hash filled in |

## Verification

**Executed:**

- **155 tests pass.** New or rewritten: table rows with the Date column, transfer row and summary line; newest first; search, wallet and category filters on the flat list; pagination with the summary covering the whole month; export of a month with signed amounts and a transfer row (exact CSV rows checked), export following filters across 61 rows, formula neutralised, only the user's own rows exported, page linking to the export with the current filters.
- **Headless Edge screenshots** at 1440px (compared with the Figma Make layout) and 390px (table scrolls sideways inside the panel; the page doesn't).
- `openspec validate add-transactions --strict`: valid, after splitting two requirements that exceeded 500 characters.

**Not executed:**

- Opening the exported file in Excel or Google Sheets.
- A real-browser check that the Export link follows filters changed without reload.

## Known gaps

- **On phones the table scrolls sideways,** as in the Figma design; a stacked mobile layout could be considered during the final UI pass.
