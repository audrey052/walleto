# Spec Delta

## ADDED Requirements

### Requirement: Budget warning after saving an expense
After a user adds or edits an expense, and its category has a limit for that month, the next page SHALL show a warning toast when the save moved that category's spent amount from below 85% of its limit to 85% or more, or from 100% or less to above 100%. The toast SHALL name the category, the percent and the month, and link to the Budget page. Saves that cross neither line, income, and transfers SHALL show no budget warning.

#### Scenario: Crossing 85%
- **WHEN** Food & drinks has spent Rp2.000.000 of a Rp2.400.000 November limit and the user adds a Rp100.000 Food & drinks expense in November
- **THEN** besides "Transaction added.", an amber toast says "Food & drinks is at 87% of its November budget." with a link to the Budget page

#### Scenario: Going over
- **WHEN** Food & drinks has spent Rp2.350.000 of Rp2.400.000 and the user adds a Rp100.000 Food & drinks expense
- **THEN** a red toast says "Food & drinks is over its November budget by Rp50.000."

#### Scenario: Already in warning
- **WHEN** Food & drinks is already at 90% and a new Rp10.000 expense brings it to 91%
- **THEN** no budget warning is shown

#### Scenario: No plan for that month
- **WHEN** the expense is dated in a month without a plan
- **THEN** no budget warning is shown

#### Scenario: Category without a limit
- **WHEN** the month has a plan but Health has no limit, and the user adds a Health expense
- **THEN** no budget warning is shown

#### Scenario: Editing moves an expense into another category
- **WHEN** the user edits an expense so it moves into Shopping and Shopping goes from 80% to 95%
- **THEN** the warning names Shopping
