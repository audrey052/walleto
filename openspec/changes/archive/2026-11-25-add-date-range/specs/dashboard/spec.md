# Spec Delta

## MODIFIED Requirements

### Requirement: Dashboard month
The Dashboard SHALL show one period at a time, the current month by default, chosen with the same period picker as the Transactions page (a whole month or a range of days up to today). Changing the period SHALL replace the page content without a full page reload and SHALL keep the period in the address, for example `?month=2026-10` or `?from=2026-11-10&to=2026-11-24`.

#### Scenario: Earlier month
- **WHEN** a user picks October 2026
- **THEN** every figure on the Dashboard is October's and the address ends with `?month=2026-10`

#### Scenario: Future month
- **WHEN** the address asks for a month after the current one
- **THEN** the Dashboard shows the current month

#### Scenario: A range of days
- **WHEN** a user picks 18 to 24 November 2026
- **THEN** income, expenses, the daily chart and Where it goes cover 18 to 24 November

### Requirement: Remaining this month
When the period is a whole calendar month that has a monthly plan, the Dashboard SHALL show "Remaining this month" as the plan minus the month's expenses, with a progress bar and "<expenses> of <plan> planned". A negative remainder SHALL be shown with a minus sign. When the month has no plan, the block SHALL NOT show the "Remaining this month" label; it SHALL say the month has no plan and link to the Budget page to set one. When the period is not a whole month, the block SHALL instead say "The monthly plan shows when a whole month is selected." with a link to the month of the period's last day.

#### Scenario: Plan and spending
- **WHEN** November's plan is Rp8.000.000 and its expenses are Rp5.847.500
- **THEN** Remaining shows Rp2.152.500 and "Rp5.847.500 of Rp8.000.000 planned"

#### Scenario: No plan
- **WHEN** the month has no category limits
- **THEN** the block says the month has no plan and offers "Set a monthly plan" linking to Budget for that month

#### Scenario: A range is not a month
- **WHEN** the period is 10 to 24 November and November has a plan
- **THEN** the block shows the note and a link to November 2026, and no remainder

### Requirement: Income and expenses
The Dashboard SHALL show Total income and Total expenses for the period. Each SHALL show its change against the previous period, as a percent with one decimal and an up or down arrow, or "—" when the previous period had none. For a whole month the previous period SHALL be the month before, labelled "vs. last month"; for another range it SHALL be the same number of days right before it, labelled "vs. previous <n> days" ("vs. previous day" for one day). Transfers and savings-goal movements SHALL NOT count.

#### Scenario: Change against last month
- **WHEN** November's expenses are Rp5.847.500 and October's were Rp5.300.000
- **THEN** Total expenses shows Rp5.847.500 and "↑ 10.3% vs. last month"

#### Scenario: Nothing last month
- **WHEN** October had no income
- **THEN** November's Total income shows "— vs. last month"

#### Scenario: Change against the previous days
- **WHEN** the period is 10 to 24 November (15 days) with expenses of Rp1.100.000, and 26 October to 9 November had Rp1.000.000
- **THEN** Total expenses shows "↑ 10.0% vs. previous 15 days"

### Requirement: Daily spending chart
The Dashboard SHALL show a bar for each day of the period with that day's expenses, and the day's date and amount when a bar is hovered or focused. Days after today SHALL be empty and today's bar SHALL be marked. When the period is a whole month with a plan, a dashed line SHALL mark the daily budget (the plan divided by the days in the month, rounded down); otherwise no daily budget line SHALL be drawn.

#### Scenario: Daily bars
- **WHEN** 12 November has expenses of Rp67.500 and Rp32.000
- **THEN** the bar for 12 November stands for Rp99.500 and its label reads "12 Nov: Rp99.500"

#### Scenario: Daily budget line
- **WHEN** November's plan is Rp9.000.000
- **THEN** the dashed line sits at Rp300.000 and is labelled with that amount

#### Scenario: Range bars
- **WHEN** the period is 18 to 24 November
- **THEN** the chart has seven bars, from 18 to 24 November, and no daily budget line

### Requirement: Where it goes
The Dashboard SHALL list the period's expense categories that have spending, largest first, each with its amount and a bar. For a whole month, each row SHALL show the percent of that category's budget used (rounded down, the same as Budget), or "No limit", with the footnote "Percentage of each category's budget". For another range, each row SHALL instead show its share of the period's expenses (rounded down), with the footnote "Share of spending in this period". Choosing a row SHALL open Transactions for the same period filtered to the category.

#### Scenario: Ordered by spending
- **WHEN** November has Food & drinks Rp2.147.500 of Rp2.800.000 and Shopping Rp1.389.500 of Rp1.600.000
- **THEN** Food & drinks is listed first with 76% and Shopping second with 86%

#### Scenario: Open a category
- **WHEN** a user chooses Shopping
- **THEN** the Transactions page opens for the same period filtered to Shopping

#### Scenario: Share in a range
- **WHEN** the period is 18 to 24 November with Food & drinks Rp600.000 and Transport Rp400.000
- **THEN** Food & drinks shows 60% and Transport 40%, under "Share of spending in this period"

### Requirement: Figures match the other pages
For the same period, the Dashboard's income, expenses and category amounts SHALL equal those on the Transactions page. For a whole month, the plan and remainder SHALL also equal those on the Budget page.

#### Scenario: Same numbers
- **WHEN** Transactions shows November expenses of Rp5.847.500 and Budget shows a plan of Rp8.000.000
- **THEN** the Dashboard shows the same expenses and Remaining Rp2.152.500

#### Scenario: Same numbers for a range
- **WHEN** Transactions for 10 to 24 November shows Expenses Rp1.100.000
- **THEN** the Dashboard for the same range shows Total expenses Rp1.100.000
