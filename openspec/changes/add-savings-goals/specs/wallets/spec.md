# Spec Delta

## MODIFIED Requirements

### Requirement: Wallets page and total balance
The Wallets page SHALL show a balance panel with the total balance of the user's active wallets, the number of active wallets and today's date, followed by a "Your wallets" table with one row per active wallet in the order they were added. Each row SHALL show the wallet name, its type and its balance, and SHALL open the Transactions page filtered to that wallet when chosen. A wallet's balance SHALL equal its starting balance, plus its income, minus its expenses, plus transfers into it, minus transfers out of it, minus money added from it to savings goals, plus money withdrawn from goals into it, over all dates. A negative balance SHALL be shown with a minus sign.

#### Scenario: Total across wallets
- **WHEN** a user has active wallets with balances Rp7.842.500, Rp647.500 and Rp485.000
- **THEN** the panel shows a total of Rp8.975.000, "Across 3 wallets", and the table has three rows

#### Scenario: No wallets yet
- **WHEN** a user with no active wallets opens the Wallets page
- **THEN** the page shows an empty state inviting them to add their first wallet, and no panel or table

#### Scenario: Balance from activity
- **WHEN** BCA started at Rp1.000.000 and has income Rp500.000, expenses Rp200.000, a transfer in of Rp50.000 and a transfer out of Rp300.000
- **THEN** BCA's row shows Rp1.050.000

#### Scenario: Balance after saving
- **WHEN** BCA holds Rp7.842.500, then Rp1.000.000 is added from BCA to a goal and Rp400.000 is withdrawn from a goal into BCA
- **THEN** BCA's row shows Rp7.242.500

#### Scenario: Negative balance
- **WHEN** a cash wallet that started at Rp20.000 has expenses of Rp50.000
- **THEN** its row shows −Rp30.000

#### Scenario: View activity
- **WHEN** a user chooses the GoPay row
- **THEN** the Transactions page opens for the current month filtered to GoPay

## ADDED Requirements

### Requirement: Money set aside in goals
When the user has money in active savings goals, the balance panel SHALL show that amount below the total, labelled "Set aside in goals", linking to the Savings goals page. It SHALL NOT be included in the total balance or the breakdown by wallet type. Completed goals SHALL NOT count.

#### Scenario: Set aside
- **WHEN** a user's wallets total Rp8.975.000 and their active goals hold Rp1.600.000
- **THEN** the panel shows the total Rp8.975.000 and "Set aside in goals Rp1.600.000"

#### Scenario: Nothing set aside
- **WHEN** a user's active goals hold Rp0, or they have no goals
- **THEN** the panel shows no set-aside line
