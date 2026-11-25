# Transactions Grouped by Day, the Figma Filter Bar and Styled Dropdowns

**Created:** 2026-11-25
**Last edited:** 2026-11-25
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `ec883a6`
**OpenSpec change:** none; `openspec/specs/transactions/spec.md` edited directly ("Transactions table", new "Grouped by day")
**Trigger:** The developer asked for the Transactions table to follow the latest Figma Make design (`TransactionsPage.tsx`, `transactions.css`), grouped by day, then for the filter bar and summary line from the same design (from a screenshot), and finally for every dropdown in the app to look better.

## Why this is recorded here

The main list of the app changes shape, and the transactions spec changes with it.

## Context

- The latest Figma Make source groups the ledger by date. Each day has a header row (date, weekday, count, daily expenses or income), and the table has no Date column. A footer line under the table says how many entries are shown and that wallet transfers are not counted as expenses.
- Figma's poetic copy ("All accounted for", "Organized by day…") is left out, per STYLE.md.

## What is built

| Area | Change |
|---|---|
| Table | columns Description, Category, Wallet, Amount (fixed widths 39/24/19/18%); one `<tbody>` per day |
| Day header | date, weekday and "N transactions" on the left. On the right: "Daily expenses Rp…" (plus "Income +Rp…" when both), or "Daily income +Rp…", or "No income or expenses" for days with only transfers or goal movements |
| Totals | per day over every entry of the period and filters, so a day split across pages shows the same header on both |
| Footer line | none: Figma's "N transactions shown" and "Wallet transfers are not counted as expenses." were built, then removed at the developer's request |
| Filter bar | four boxes on the page background (Figma `.ledger-filter-bar`, columns 1.15/1/0.95/1.25, two columns on phones): the date picker in a new "bar" look (calendar and label; no month arrows, at the developer's request), category and wallet filters with an icon and a chevron, and search. The filter form uses `display: contents` so it shares the grid with the date picker, which has its own form |
| Filter menus | category and wallet open a styled menu (`selectMenu` in `static/js/app.js`, `finance/_select_menu.html`). It shows colour dots, Expense/Income headings and a tick on the current item. The native select stays hidden but keeps the value and fires `change`, so HTMX filtering and the no-JavaScript form are unchanged |
| All form dropdowns | every `<select class="input">` (transaction, transfer, goal, wallet and budget forms; modals included, via `htmx:load`) gets a styled button and menu. The menu is fixed to the screen so a scrolling modal cannot clip it, and it opens upward when there is no room below. Keyboard: arrows, Escape (closes the menu only, not the modal), Tab. The hidden native select keeps the value, the label link, validation and `change`; the transfer form's swap now fires `change` so the labels follow |
| No coloured dots | removed from chips everywhere (categories, Transfer, Savings goal, goal status), from wallet names in the Transactions table, and from the filter menus, at the developer's request; Home keeps its dots |
| Summary line | under the bar: "N transactions • <period>" (and Clear filters) on the left, "Income +Rp… • Expenses Rp…" on the right |
| Heading | Export CSV moved next to Add transaction |
| Rows | unchanged behaviour (open for edit, goal rows open the goal, AI label); transfer and income icons tinted green as in Figma |

## Requirements this establishes

1. **Transactions are grouped by day with a daily total.**

## Files changed

| File | Change |
|---|---|
| `finance/views_activity.py` | `day_groups(page_entries, all_entries)` and `day_groups` in the context |
| `templates/finance/transactions.html` | grouped table; filter bar, summary line and heading actions |
| `templates/components/period_picker.html` | `picker_variant="bar"` look for the filter bar, without arrows (Home keeps the compact picker with arrows) |
| `templates/finance/_select_menu.html` (new), `static/js/app.js` | styled filter menus; the form-select enhancer; the transfer swap fires `change` |
| `openspec/specs/period-picker/spec.md` | "Month arrows": arrows on Home only |
| `static/src/app.css` | `.ledger-*`, `.filter-bar`, `.filter-box`, `.dot-sep` styles; the bar's date popover opens from the left |
| `finance/tests/test_activity.py` | grouped rows, day totals, "No income or expenses", footer, a day split across pages |
| `openspec/specs/transactions/spec.md` | "Transactions table" reworded; new "Grouped by day" |
| `openspec/commits/README.md`, `archive-date-range-and-savings-goals.md` | `ec883a6` filled in, this record |

## Verification

**Executed:**

- `python manage.py test`: 452 tests OK.
- `openspec validate transactions --type spec --strict`: valid.
- Edge headless, demo account, at 1440px and the narrowest Edge window (519px):
  - the filter bar matches the screenshot (four boxes; two rows on phones);
  - choosing a wallet updates the list and the address (`wallet=…`) without a full load;
  - the category menu lists 10 items under EXPENSE and INCOME; choosing Transport gives `category=3` and closes the menu, with no full load; the wallet menu shows the five wallets with their colours;
  - the bar has no month arrows;
  - in the Add transaction modal both selects are styled; the category menu shows EXPENSE/INCOME and is not clipped by the modal; choosing Transport sets the native select; Escape closes the menu and keeps the modal open;
  - in the transfer modal, choosing BCA then ⇄ swaps both labels (GoPay → BCA) and the balance preview follows;
  - the date popover opens under the box (265–565px at 1440px, 17–317px on phones);
  - no horizontal page scroll.
- Edge headless, demo account: 15 day groups for November. The first reads "23 Nov 2026 · Monday · 3 transactions · Daily expenses Rp237.000", and a goal-only day reads "No income or expenses". No horizontal page scroll at 1440px or 390px; at 390px the table scrolls inside its panel, as in Figma (min width 650px).

**Not executed:**

- None.

## Known gaps

- **On phones the daily total sits at the right of the scrolling table,** so it shows after a sideways scroll, as in the Figma design.
