# Spec Delta

## Purpose

Lets a user set money aside from their wallets for several things they are saving toward, and see how far along each goal is and whether they are on pace to reach it by its deadline.

## ADDED Requirements

### Requirement: Create a goal
A signed-in user SHALL be able to create a goal with a name (1 to 40 characters), a target of at least Rp1.000 and an optional deadline after today. The name SHALL be unique among the user's active goals, ignoring letter case. The goal's start date SHALL be the day it is created, in Jakarta time. A toast SHALL say "Goal created."

#### Scenario: New goal
- **WHEN** on 18 November 2026 a user creates "Bali trip" with target "6.000.000" and deadline 30 June 2027
- **THEN** the goal appears with Rp0 saved of Rp6.000.000, start date 18 Nov 2026, and a toast says "Goal created."

#### Scenario: Deadline in the past
- **WHEN** the deadline is today or earlier
- **THEN** the goal is not created and the form says the deadline must be after today

#### Scenario: Duplicate name
- **WHEN** the user already has an active goal "Laptop" and creates "laptop"
- **THEN** the goal is not created and the form says the name is already used

### Requirement: Add money to a goal
A user SHALL be able to add money to a goal from one of their active wallets, with an amount greater than zero, a date (default today, not in the future and not before the goal's start date) and an optional note. The amount SHALL NOT be larger than the wallet's current balance. The wallet's balance SHALL drop by the amount and the goal's saved amount SHALL rise by it. A toast SHALL say "Added to <goal>."

#### Scenario: Deposit
- **WHEN** BCA holds Rp7.842.500 and the user adds "1.000.000" from BCA to "Bali trip"
- **THEN** BCA's balance becomes Rp6.842.500, Bali trip shows Rp1.000.000 saved, and a toast says "Added to Bali trip."

#### Scenario: Not enough in the wallet
- **WHEN** GoPay holds Rp300.000 and the user adds "500.000" from GoPay
- **THEN** nothing is saved and the form says "Not enough in GoPay. Choose another wallet or a smaller amount."

### Requirement: Withdraw money from a goal
A user SHALL be able to move money from a goal back to one of their active wallets, with the same amount, date and note rules as adding money. The amount SHALL NOT be larger than the goal's saved amount. The goal's saved amount SHALL drop and the wallet's balance SHALL rise by the amount. A toast SHALL say "Moved back to <wallet>."

#### Scenario: Withdraw
- **WHEN** Bali trip holds Rp1.000.000 and the user withdraws "400.000" to GoPay
- **THEN** Bali trip shows Rp600.000 saved and GoPay's balance rises by Rp400.000

#### Scenario: More than the goal holds
- **WHEN** Bali trip holds Rp600.000 and the user withdraws "700.000"
- **THEN** nothing is saved and the form says the goal holds only Rp600.000

### Requirement: Goal movements are not income or expenses
Deposits and withdrawals SHALL NOT count as income or expenses, SHALL NOT count toward any budget, and SHALL NOT change the sum of the user's wallet balances plus the amount set aside in goals.

#### Scenario: Budget unaffected
- **WHEN** a user adds Rp1.000.000 to a goal in November
- **THEN** November's expenses and every budget category's spent amount are unchanged

### Requirement: Goal progress
For each goal the app SHALL show the saved amount (deposits minus withdrawals), the target, the percent saved rounded down, and the amount to go (target minus saved, never below Rp0). When the saved amount reaches the target, the goal SHALL show "Your goal, reached." instead of the percent line.

#### Scenario: Partway
- **WHEN** a goal of Rp6.000.000 has Rp1.500.000 saved
- **THEN** it shows 25% of the way there and Rp4.500.000 to go

#### Scenario: Reached
- **WHEN** a goal of Rp6.000.000 has Rp6.000.000 saved
- **THEN** it shows "Your goal, reached." and Rp0 to go

### Requirement: Goal status
A goal with a deadline that is not reached SHALL show a status. Before the deadline it is "On track" when saved × total days ≥ target × elapsed days, else "Behind". Total days run from the start date to the deadline and elapsed days from the start date to today. After the deadline it is "Past deadline". A goal without a deadline or already reached SHALL show no status.

#### Scenario: On track
- **WHEN** a Rp3.000.000 goal started 1 September 2026 with deadline 30 November 2026 (90 days) has Rp2.700.000 saved on 18 November (78 days elapsed)
- **THEN** it shows "On track", because 2.700.000 × 90 ≥ 3.000.000 × 78

#### Scenario: Behind
- **WHEN** the same goal has Rp2.500.000 saved on 18 November
- **THEN** it shows "Behind", because 2.500.000 × 90 < 3.000.000 × 78

#### Scenario: Past deadline
- **WHEN** the deadline was 31 October 2026, the goal is not reached, and today is 18 November 2026
- **THEN** it shows "Past deadline"

### Requirement: Amount needed per month
For a goal with a deadline that is not reached and not past its deadline, the app SHALL show the amount needed per month. This is the amount to go divided by the months left, rounded up to the next Rupiah. Months left count the current month and the deadline's month.

#### Scenario: Per month
- **WHEN** on 18 November 2026 a Rp6.000.000 goal with Rp0 saved has deadline 30 June 2027 (November to June, 8 months)
- **THEN** it shows Rp750.000 a month

### Requirement: Savings goals page
The Savings goals page SHALL feature the main goal in a large card with its name, saved of target, progress bar, progress line, amount to go, deadline and status, and the actions "Add to this goal" and "Edit goal". When the main goal has a monthly amount, a line below the card SHALL say "Put aside <amount> a month to reach your target by <Month YYYY>." The other active goals SHALL be listed below, without a heading, with their progress, saved of target, deadline and status.

#### Scenario: Several goals
- **WHEN** a user has active goals "Bali trip", "Emergency fund" and "Laptop"
- **THEN** one of them is shown in the large card and the other two are listed below it

#### Scenario: Open a goal
- **WHEN** a user chooses "Laptop" in the list
- **THEN** the Laptop goal detail page opens

### Requirement: Main goal
The user's active goals SHALL keep an order that the user sets by dragging a goal's handle, or by focusing the handle and pressing the up or down arrow key. The first goal in the order SHALL be the main goal, shown in the large card; the others follow in order. The order SHALL be saved right away. A new or reopened goal SHALL go to the end of the order.

#### Scenario: Drag a goal to the top
- **WHEN** the order is Laptop, Emergency fund, Bali trip and the user drags Emergency fund above Laptop
- **THEN** Emergency fund is shown in the large card, followed by Laptop and Bali trip, also after a reload

#### Scenario: Keyboard
- **WHEN** the user focuses Emergency fund's handle and presses the up arrow key
- **THEN** Emergency fund moves one place up and the new order is saved

#### Scenario: New goal
- **WHEN** a user with goals Laptop and Bali trip creates "Emergency fund"
- **THEN** Emergency fund is listed after Bali trip

### Requirement: No goals yet
When the user has no active goals, the page SHALL show an empty state inviting them to create their first goal, plus the Completed section if any goal was completed.

#### Scenario: First visit
- **WHEN** a user with no goals opens Savings goals
- **THEN** the page shows an empty state with a "Create a goal" action and no card or list

### Requirement: Goal detail page
Each goal SHALL have a detail page with its progress, status and monthly amount, its actions, a line chart and its history. The chart SHALL show the saved amount at the end of each day from the start date to today. When the goal has a deadline, the chart SHALL also show the plan line from Rp0 on the start date to the target on the deadline. The history SHALL list deposits and withdrawals newest first, each with its wallet, date, note and signed amount.

#### Scenario: Chart with a plan
- **WHEN** a user opens a goal with a deadline and three deposits
- **THEN** the chart shows the saved line stepping up on the three deposit dates and a straight plan line to the target at the deadline

#### Scenario: History
- **WHEN** the goal has a deposit of Rp1.000.000 from BCA and a withdrawal of Rp400.000 to GoPay
- **THEN** the history lists "From BCA" +Rp1.000.000 and "To GoPay" −Rp400.000, newest first

### Requirement: Edit and delete goals and movements
A user SHALL be able to edit a goal's name, target and deadline with the creation rules; an unchanged past deadline may be kept. A goal SHALL only be deletable, after confirming, when its saved amount is Rp0, and deleting it SHALL NOT change any wallet balance. A deposit or withdrawal SHALL be deletable after confirming, unless that would make the goal's saved amount negative.

#### Scenario: Delete an empty goal
- **WHEN** a goal received Rp500.000 from BCA, Rp500.000 was withdrawn to GoPay, and the user deletes it and confirms
- **THEN** the goal leaves the page, a toast says "Goal deleted.", BCA and GoPay keep their balances, and both movements stay in the Transactions list without a link

#### Scenario: Delete a goal that holds money
- **WHEN** a goal holds Rp600.000 and the user chooses delete
- **THEN** the goal is kept and the user is told to move the Rp600.000 back to a wallet first, with a link to withdraw it

#### Scenario: Delete a deposit
- **WHEN** the user deletes a Rp1.000.000 deposit from BCA and confirms
- **THEN** the goal's saved amount drops by Rp1.000.000 and BCA's balance rises by Rp1.000.000

### Requirement: Complete a goal
A reached goal SHALL offer "Mark as complete". A completed goal SHALL leave the active goals, appear in a "Completed" section with its saved amount and completion date, and accept no deposits or withdrawals. Its money SHALL count as used: it stays out of the wallets and out of the amount set aside in goals. A completed goal SHALL be reopenable, which makes it active again.

#### Scenario: Complete
- **WHEN** a user marks the reached "Laptop" goal (Rp12.000.000 saved) as complete
- **THEN** Laptop moves to Completed, and the amount set aside in goals drops by Rp12.000.000 while wallet balances stay the same

#### Scenario: Not reached
- **WHEN** a goal is not reached
- **THEN** "Mark as complete" is not offered

### Requirement: Goals are private
A user SHALL only see and change their own goals, deposits and withdrawals, and a deposit or withdrawal SHALL only use the user's own wallets. Requests for another user's goal or movement SHALL respond as if it did not exist.

#### Scenario: Another user's goal
- **WHEN** a user opens the address of another user's goal
- **THEN** the response is "not found"

#### Scenario: Another user's wallet
- **WHEN** a deposit form is submitted with another user's wallet
- **THEN** nothing is saved and the form says to choose a wallet
