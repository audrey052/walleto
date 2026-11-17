# Proposal

## Why

Walleto records where money goes, but not where it should go. With a monthly spending plan, people can see while the month is still running how much is left, how much they can spend per day, and which categories are getting close to their limit. After this MVP Walleto covers a full personal-finance loop (wallets, transactions, budget) and can be used every day.

## What Changes

- Add **category budgets**: a limit per expense category per month, set by the user (for example Food & drinks Rp3.000.000 for November 2026).
- The **monthly plan** is the sum of the month's category limits. It is computed, never typed in twice.
- **Quick start from one number.** For a month with no limits yet, the user can enter one total. It is split across the expense categories by default shares, and the user can then adjust each limit.
- **"Edit monthly plan" rescales.** Entering a new total changes every existing limit in proportion to the user's own limits, and the limits still add up exactly to the new total. This follows the Figma design ("Your category limits will adjust proportionally").
- **Edit or remove a single category's limit** in a modal. Categories without a limit are listed as "No limit set" with a "Set limit" action.
- **Spent, remaining and status are computed by code** from the month's expense transactions. Status per category and for the whole plan: normal below 85%, warning from 85% to 100% (amber, "Getting close to your limit"), over above 100% (red).
- **Days left and remaining per day** for the selected month: remaining ÷ days left, today included.
- Replace the Budget placeholder with a page laid out as in the Figma design:
  - A heading with a month picker and an "Edit monthly plan" button.
  - An overview panel with the plan total, the amount left, the percent spent with a progress bar, days left and the amount per day.
  - A list headed "A place for every Rupiah" with one row per budgeted category: icon, name, status line, progress bar, spent of limit, percent, and an edit action.
- A **"Copy last month's budget"** button when the selected month has no limits but the month before does. It copies every category limit.
- A **budget warning toast on Transactions**: after an expense is added or edited, a warning appears when it takes its category to 85% or past 100% of that month's limit.
- The shared progress bar switches to amber at **85%** instead of 90%, and can use the category color in the normal state. docs/STYLE.md is updated to match.
- The demo account gets category budgets for each of its three months.

Out of scope for this MVP:
- Changing the default shares used for the first split.
- Rolling unspent money over to the next month.
- Budgets per wallet, or for income categories.
- Budget alerts in the topbar bell, by email, or on the dashboard (MVP 5).
- AI budget advice (MVP 7).

## Capabilities

### New Capabilities
- `budgets`: category limits per month, the monthly plan as their sum, the first split and proportional rescale, spent / remaining / per-day figures and status, the Budget page, editing, removing and copying limits, and budget privacy.

### Modified Capabilities
- `transactions`: saving an expense can show a budget warning toast.
- `demo-account`: demo data now includes category budgets for each month.

## Impact

- `finance/models.py`: a new `Budget` model (`user`, `category`, `month`, `limit`) and a `budget_share` field on `Category`. New migration `finance.0004` that adds both and sets shares for the default categories.
- New budget calculation module with unit tests (`finance/budgets.py`).
- New views, forms, URLs and templates for the Budget page and its modals. Budget moves from the `core` placeholder to `finance:budget`.
- `finance/views_activity.py`: the warning check after a transaction is saved.
- `templates/components/progress.html`, `templates/components/toasts.html` (warning style), docs/STYLE.md: new 85% threshold, category color, and warning toast.
- `finance/demo.py`: demo budgets.
- No new dependencies.
