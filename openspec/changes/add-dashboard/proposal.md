# Proposal

## Why

The home page is still a "coming soon" placeholder. Today, answering "how is my month going?" means opening Budget, Transactions and Wallets one by one. The Dashboard puts the month's key figures in one place, and its monthly summary is the base the Assistant (MVP 7) will reuse. MVP 5 in WORKPLAN.md. The developer chose the full version from the Figma Make Dashboard over a slim one.

## What Changes

- **Monthly summary service.** One function returns every Dashboard figure for a user and a month. Figures are computed by code and tested, and reused later by the Assistant.
- **Month picker.** The same prev/next picker as Transactions: the current month and earlier. Switching months swaps the page content without a full reload and keeps the month in the address.
- **Remaining this month:**
  - the monthly plan (from Budget) minus the month's expenses;
  - a projection line ("Enough for 37 days of meals at Rp50.000 a day", "Over your plan by Rp…");
  - for past months, how the month ended;
  - plan progress, "Rp… of Rp… planned";
  - when the month has no plan, a "Set a monthly plan" link instead.
- **Total income and Total expenses.** The month's totals with the change against the month before, to one decimal ("—" when the month before has none). No trend line.
- **Daily spending chart.** One bar per day of the month for expenses, with a dashed line at the daily budget (plan ÷ days in the month) and the day's amount on hover or focus. Today is marked in the current month.
- **Where it goes.** Expense categories with spending, largest first:
  - bar and amount for each;
  - the percent of each category's budget used;
  - a row opens Transactions filtered to that category and month.
- **Layout after the Figma Dashboard;** copy follows docs/STYLE.md. The poetic eyebrow ("YOUR MONTH AT A GLANCE"), the poetic projection lines and "A small observation:" are not used.
- **The Dashboard stays the first page after sign-in.** The `core` placeholder view is replaced.

Out of scope for this MVP:
- The Figma insight row ("A small observation: … Let's take a look"); the developer removed it.
- Budget alerts in the topbar bell.
- Savings goals or wallet balances on the Dashboard.
- A wallet filter and a recent-transactions list (in the Figma Dashboard; the developer removed both).
- Choosing a custom date range.
- Exporting the Dashboard.

## Capabilities

### New Capabilities
- `dashboard`: the monthly summary figures, month picker, Remaining with projection, income and expenses with change, daily spending chart, Where it goes, and Dashboard privacy.

### Modified Capabilities
None. `app-shell` already makes the home address the Dashboard. The Dashboard stops being a placeholder by being built, as Wallets, Budget and Savings goals did.

## Impact

- New `finance/summary.py` (the service) with unit tests, `finance/views_dashboard.py`, and `templates/finance/dashboard.html` with partials.
- `core/urls.py` / `core/views.py`: the route keeps its name `core:dashboard` (19 references, including the sign-in redirect) and address `/`, but now calls the finance Dashboard view instead of the placeholder.
- No trend lines on the income and expense cards (removed by the developer), so `{% sparkline %}` is not brought back.
- The daily chart is server-rendered HTML bars, as in the Figma `SpendingChart`, with no JavaScript library.
- Reuses `finance/budgets.py` (plan, category limits), `finance/months.py`, and the Transaction querysets.
- No new dependencies.
