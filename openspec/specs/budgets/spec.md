# budgets Specification

## Purpose
Lets a user give each month a spending plan made of category limits, see spent, remaining and per-day amounts while the month runs, and get a warning before a category runs out.

## Requirements

### Requirement: Category limits
A signed-in user SHALL be able to set, change and remove a limit for any expense category they can see, per month. A limit is a whole-Rupiah amount of at least Rp1.000. A category has at most one limit per month per user. Income categories SHALL NOT accept a limit.

#### Scenario: Set a limit
- **WHEN** a user sets Food & drinks to "3.000.000" for November 2026
- **THEN** the Budget page for November 2026 shows Food & drinks with a Rp3.000.000 limit

#### Scenario: Change a limit
- **WHEN** the user later saves "2.500.000" for Food & drinks in November 2026
- **THEN** Food & drinks has one limit for November, of Rp2.500.000

#### Scenario: Remove a limit
- **WHEN** the user removes the Food & drinks limit for November 2026
- **THEN** Food & drinks shows "No limit set" and the plan total drops by its old limit

#### Scenario: Too small
- **WHEN** the user saves "500" as a limit
- **THEN** the limit is not saved and the form says the limit must be at least Rp1.000

### Requirement: Monthly plan is the sum of limits
The monthly plan SHALL equal the sum of that month's category limits. A month with no limits SHALL have no plan.

#### Scenario: Plan total
- **WHEN** November 2026 has limits of Rp3.000.000, Rp1.500.000 and Rp500.000
- **THEN** the plan for November is Rp5.000.000

### Requirement: First split from one total
For a month with no limits, the user SHALL be able to enter one total of at least Rp100.000. It SHALL be split across every expense category they can see by fixed default shares, in whole Rupiah that add up exactly to the total.

#### Scenario: Split of a new plan
- **WHEN** November has no limits and the user enters "8.000.000", and Food & drinks has a 30% default share
- **THEN** Food & drinks gets a Rp2.400.000 limit and all limits add up to Rp8.000.000

#### Scenario: Limits add up
- **WHEN** the user enters "8.000.001"
- **THEN** the limits are whole Rupiah amounts that add up to exactly Rp8.000.001

### Requirement: Rescale the plan
For a month that has limits, entering a new total (at least Rp100.000) SHALL change every existing limit in proportion to the current limits, in whole Rupiah that add up exactly to the new total. Categories without a limit SHALL stay without one.

#### Scenario: Proportional change
- **WHEN** November has Food & drinks Rp3.000.000 and Transport Rp1.000.000, and the user sets the plan to Rp6.000.000
- **THEN** Food & drinks becomes Rp4.500.000 and Transport Rp1.500.000

#### Scenario: Unbudgeted category stays unbudgeted
- **WHEN** Health has no November limit and the user rescales the plan
- **THEN** Health still shows "No limit set"

### Requirement: Spent and remaining
Spent for a category SHALL be the sum of the user's expense transactions in that category dated in that month, across all wallets, including archived ones. Transfers and income SHALL NOT count. Spent for the plan SHALL be the sum of all expense transactions in the month, including categories without a limit. Remaining SHALL be the limit (or plan) minus spent, and can be negative.

#### Scenario: Spent in a category
- **WHEN** a user has expenses of Rp67.500 and Rp24.000 in Food & drinks in November and Rp50.000 on 31 October
- **THEN** Food & drinks shows Rp91.500 spent for November

#### Scenario: Transfers do not count
- **WHEN** the user moves Rp500.000 from BCA to GoPay in November
- **THEN** the amount spent for November does not change

#### Scenario: Unbudgeted spending counts toward the plan
- **WHEN** Health has no limit and Rp300.000 of Health expenses in November
- **THEN** the November plan's spent amount includes the Rp300.000

#### Scenario: Over the plan
- **WHEN** the plan is Rp8.000.000 and Rp8.200.000 has been spent
- **THEN** remaining is −Rp200.000 and the page says the month is Rp200.000 over plan

### Requirement: Budget status
Each budgeted category and the plan as a whole SHALL have a status from the percent spent (spent ÷ limit × 100): normal below 85%, warning from 85% up to and including 100%, and over above 100%. Warning SHALL be shown in amber with "Getting close to your limit"; over SHALL be shown in red with "Over by" and the amount; normal SHALL say "A little breathing room". Percentages SHALL be shown rounded down.

#### Scenario: Normal
- **WHEN** a category has spent Rp1.359.999 of a Rp1.600.000 limit (just under 85%)
- **THEN** its status is normal, its bar uses the category color, and it shows 84%

#### Scenario: Warning at 85%
- **WHEN** a category has spent exactly 85% of its limit
- **THEN** its status is warning, its bar and percent are amber, and it says "Getting close to your limit"

#### Scenario: Exactly the limit
- **WHEN** a category has spent exactly 100% of its limit
- **THEN** its status is still warning

#### Scenario: Over
- **WHEN** a category has spent Rp1.700.000 of a Rp1.600.000 limit
- **THEN** its status is over, its bar is full and red, it shows 106%, and it says "Over by Rp100.000"

### Requirement: Days left and amount per day
For the current month, days left SHALL count today and every remaining day of the month in Jakarta time. For a future month it SHALL be every day of that month, and for a past month zero. When days left is above zero and remaining is above zero, the page SHALL show remaining ÷ days left per day, rounded down to whole Rupiah. Otherwise it SHALL show no per-day amount.

#### Scenario: Middle of the month
- **WHEN** today is 17 November 2026 and Rp2.800.000 of the plan remains
- **THEN** the page shows 14 days left and Rp200.000 a day

#### Scenario: Last day of the month
- **WHEN** today is 30 November 2026 and Rp150.000 remains
- **THEN** the page shows 1 day left and Rp150.000 a day

#### Scenario: February
- **WHEN** today is 1 February 2027
- **THEN** the page shows 28 days left

#### Scenario: Leap-year February
- **WHEN** today is 1 February 2028
- **THEN** the page shows 29 days left

#### Scenario: Nothing left
- **WHEN** the plan is already spent or over
- **THEN** the page shows the days left but no amount per day

#### Scenario: Past month
- **WHEN** the user views October 2026 on 17 November 2026
- **THEN** no days left and no amount per day are shown

### Requirement: Budget page
The Budget section SHALL show one month at a time, chosen with a month picker (`?month=YYYY-MM`, default the current month, up to one month ahead). With a plan, the page SHALL show an overview (plan total, amount left, percent spent with a progress bar, spent of plan, days left, amount per day) and a list headed "A place for every Rupiah" with one row per budgeted category, sorted by amount spent, highest first, followed by the categories without a limit.

#### Scenario: Category row
- **WHEN** Food & drinks has spent Rp2.147.500 of a Rp2.400.000 November limit
- **THEN** its row shows the Food & drinks icon, name, status line, progress bar, "Rp2.147.500 of Rp2.400.000", 89%, and an edit action

#### Scenario: Category without a limit
- **WHEN** Health has no November limit
- **THEN** it is listed after the budgeted rows with its spent amount, "No limit set" and a "Set limit" action

#### Scenario: Next month
- **WHEN** today is 17 November 2026 and the user opens December 2026
- **THEN** the page shows December 2026 and the next-month arrow is disabled

#### Scenario: Invalid month
- **WHEN** the address has `?month=2026-13` or a month more than one month ahead
- **THEN** the page shows the current month

### Requirement: Month without a plan
When the selected month has no limits, the Budget page SHALL show an empty state with "Set monthly plan". When the month before has limits, it SHALL also offer "Copy last month's budget", which copies every category limit to the selected month and shows a toast.

#### Scenario: No plan, nothing to copy
- **WHEN** a new user opens the Budget page
- **THEN** they see an empty state with "Set monthly plan" and no copy button

#### Scenario: Copy last month
- **WHEN** October 2026 has Food & drinks Rp3.000.000 and Transport Rp1.000.000, November has no limits, and the user chooses "Copy last month's budget" on November
- **THEN** November gets the same two limits and a toast says "Copied October's budget."

#### Scenario: Copy only by form submission
- **WHEN** the copy address is opened with a plain GET request
- **THEN** no limit is created

### Requirement: Budget modals
"Edit monthly plan" (or "Set monthly plan") SHALL open a modal titled "Give your month a plan." with the note "Your category limits will adjust proportionally." and one amount field filled with the current total. Each category row SHALL open an "Edit budget" modal with the limit and a "Remove limit" action. Saving SHALL show a toast. Every form SHALL also work as a normal page without JavaScript.

#### Scenario: Save the plan
- **WHEN** the user enters "9.000.000" in the plan modal for November 2026 and saves
- **THEN** the modal closes, the page shows a Rp9.000.000 plan with rescaled limits, and the toast "Your monthly spending plan has been updated." appears

#### Scenario: Save a category limit
- **WHEN** the user sets Food & drinks to "3.000.000" in its modal
- **THEN** the modal closes, the row and the plan total update, and the toast "Food & drinks budget updated." appears

### Requirement: Budgets are private
A user SHALL only see and change their own limits. Spent amounts SHALL only include the user's own transactions. Another user's limit SHALL never be shown, changed, removed or copied, including by changing an ID in the address.

#### Scenario: Other users' spending
- **WHEN** another user has Rp5.000.000 of Food & drinks expenses in November
- **THEN** the first user's Food & drinks spent for November does not include them

#### Scenario: Other users' limits
- **WHEN** a user opens the edit or remove address of another user's limit
- **THEN** the response is "not found" and the limit is unchanged

#### Scenario: Separate plans
- **WHEN** another user has November limits and the first user has none
- **THEN** the first user sees the empty state, and setting a plan creates separate limits without changing the other user's
