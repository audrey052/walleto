# dashboard Specification

## Purpose
Gives a signed-in user one page that shows how a month is going: what is left of the plan, income and expenses against the month before, and spending day by day and by category.

## Requirements

### Requirement: Dashboard month
The Dashboard SHALL show one month at a time, the current month by default, with the same previous and next month picker as the Transactions page. Later months than the current one SHALL NOT be shown. Changing the month SHALL replace the page content without a full page reload and SHALL keep the month in the address, for example `?month=2026-10`.

#### Scenario: Earlier month
- **WHEN** a user picks October 2026
- **THEN** every figure on the Dashboard is October's and the address ends with `?month=2026-10`

#### Scenario: Future month
- **WHEN** the address asks for a month after the current one
- **THEN** the Dashboard shows the current month

### Requirement: Remaining this month
When the month has a monthly plan, the Dashboard SHALL show "Remaining this month" as the plan minus the month's expenses, with a progress bar and "<expenses> of <plan> planned". A negative remainder SHALL be shown with a minus sign. When the month has no plan, the block SHALL NOT show the "Remaining this month" label; it SHALL say the month has no plan and link to the Budget page to set one.

#### Scenario: Plan and spending
- **WHEN** November's plan is Rp8.000.000 and its expenses are Rp5.847.500
- **THEN** Remaining shows Rp2.152.500 and "Rp5.847.500 of Rp8.000.000 planned"

#### Scenario: No plan
- **WHEN** the month has no category limits
- **THEN** the block says the month has no plan and offers "Set a monthly plan" linking to Budget for that month

### Requirement: Projection line
In the current month, the line under Remaining SHALL say how many days of meals the remainder covers at Rp50.000 a day, rounded down: "Enough for <n> days of meals at Rp50.000 a day", "Not enough for a day of meals at Rp50.000" when it covers less than one day, or "Over your plan by <amount>" when the remainder is negative.

#### Scenario: Over the plan
- **WHEN** November's plan is Rp8.000.000 and its expenses are Rp8.250.000
- **THEN** the line says "Over your plan by Rp250.000"

#### Scenario: Days of meals
- **WHEN** the plan is Rp8.000.000 and expenses are Rp6.000.000
- **THEN** Rp2.000.000 covers 40 days and the line says "Enough for 40 days of meals at Rp50.000 a day"

#### Scenario: Less than a day
- **WHEN** Rp20.000 of the plan is left
- **THEN** the line says "Not enough for a day of meals at Rp50.000"

### Requirement: How a past month ended
For a month before the current one, the line under Remaining SHALL say how the month ended: "Ended <Month> with <amount> left", or "Ended <Month> <amount> over plan" when expenses passed the plan.

#### Scenario: Past month
- **WHEN** a user views October, whose expenses were Rp300.000 under its plan
- **THEN** the line says "Ended October with Rp300.000 left"

### Requirement: Income and expenses
The Dashboard SHALL show Total income and Total expenses for the month. Each SHALL show its change against the month before, as a percent with one decimal and an up or down arrow, or "—" when the month before had none. Transfers and savings-goal movements SHALL NOT count.

#### Scenario: Change against last month
- **WHEN** November's expenses are Rp5.847.500 and October's were Rp5.300.000
- **THEN** Total expenses shows Rp5.847.500 and "↑ 10.3% vs. last month"

#### Scenario: Nothing last month
- **WHEN** October had no income
- **THEN** November's Total income shows "— vs. last month"

### Requirement: Daily spending chart
The Dashboard SHALL show a bar for each day of the month with that day's expenses, a dashed line at the daily budget (the plan divided by the days in the month, rounded down), and the day's date and amount when a bar is hovered or focused. In the current month, days after today SHALL be empty and today's bar SHALL be marked. Without a plan, no daily budget line SHALL be drawn.

#### Scenario: Daily bars
- **WHEN** 12 November has expenses of Rp67.500 and Rp32.000
- **THEN** the bar for 12 November stands for Rp99.500 and its label reads "12 Nov: Rp99.500"

#### Scenario: Daily budget line
- **WHEN** November's plan is Rp9.000.000
- **THEN** the dashed line sits at Rp300.000 and is labelled with that amount

### Requirement: Where it goes
The Dashboard SHALL list the month's expense categories that have spending, largest first, each with its amount, a bar and the percent of that category's budget used (rounded down, the same as Budget), with the footnote "Percentage of each category's budget"; a category without a limit SHALL show "No limit". Choosing a row SHALL open Transactions for that month filtered to the category.

#### Scenario: Ordered by spending
- **WHEN** November has Food & drinks Rp2.147.500 of Rp2.800.000 and Shopping Rp1.389.500 of Rp1.600.000
- **THEN** Food & drinks is listed first with 76% and Shopping second with 86%

#### Scenario: Open a category
- **WHEN** a user chooses Shopping
- **THEN** the Transactions page opens for the same month filtered to Shopping

### Requirement: Figures match the other pages
For the same month, the Dashboard's income, expenses, plan, remainder and category amounts SHALL equal those on the Transactions and Budget pages.

#### Scenario: Same numbers
- **WHEN** Transactions shows November expenses of Rp5.847.500 and Budget shows a plan of Rp8.000.000
- **THEN** the Dashboard shows the same expenses and Remaining Rp2.152.500

### Requirement: Dashboard is private
The Dashboard SHALL only count the signed-in user's own transactions and budget.

#### Scenario: Another user's spending
- **WHEN** another user has expenses and a plan in November
- **THEN** none of them appear in the signed-in user's November figures
