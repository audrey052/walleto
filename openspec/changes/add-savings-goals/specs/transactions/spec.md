# Spec Delta

## ADDED Requirements

### Requirement: Goal movements in the Transactions list
Goal deposits and withdrawals SHALL be listed with the month's transactions and transfers as neutral rows. A deposit shows "<Wallet> → <Goal>", a withdrawal "<Goal> → <Wallet>", "Savings goal" in the Category column, the wallet, and the amount without a plus or minus sign. They SHALL count as entries in the summary but not as income or expenses. Choosing one SHALL open its goal's detail page, unless the goal was deleted.

#### Scenario: Deposit in the list
- **WHEN** Rp1.000.000 was added from BCA to "Bali trip" on 18 November
- **THEN** the table shows a "BCA → Bali trip" row dated 18 Nov 2026 with Rp1.000.000 and category "Savings goal", and November's expenses do not include it

#### Scenario: Filters
- **WHEN** a user filters by BCA, then by the Food & drinks category
- **THEN** the BCA filter keeps the "BCA → Bali trip" row and the category filter hides it

### Requirement: Goal movements in the CSV export
In the export, a goal deposit or withdrawal SHALL appear with type "Savings", the same "From → To" text as the list as its description, the wallet's name as its wallet, and an unsigned amount.

#### Scenario: Export a deposit
- **WHEN** November has a Rp1.000.000 deposit from BCA to "Bali trip" and the user exports November
- **THEN** the file has a row with type "Savings", description "BCA → Bali trip", wallet "BCA" and amount 1000000
