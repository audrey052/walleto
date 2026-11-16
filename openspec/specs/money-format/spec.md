# money-format Specification

## Purpose
Defines one consistent way to display Rupiah amounts everywhere in Walleto, so that numbers read the same on every page and line up in tables.

## Requirements

### Requirement: Rupiah display format
Every amount SHALL be shown as "Rp" followed by the whole number with a dot as the thousands separator and no decimals and no space after "Rp". Amounts SHALL use tabular (equal-width) digits so columns line up.

#### Scenario: Typical amount
- **WHEN** the amount 847500 is displayed
- **THEN** it reads "Rp847.500"

#### Scenario: Large amount
- **WHEN** the amount 12500000 is displayed
- **THEN** it reads "Rp12.500.000"

#### Scenario: Zero
- **WHEN** the amount 0 is displayed
- **THEN** it reads "Rp0"

### Requirement: Income and expense signs
Where an amount represents money in or out, an expense SHALL be prefixed with the minus sign "−" (U+2212) and an income SHALL be prefixed with "+" and shown in the accent color. Neutral amounts such as balances SHALL have no sign unless they are negative.

#### Scenario: Expense row
- **WHEN** an expense of 67500 is displayed in a transaction list
- **THEN** it reads "−Rp67.500"

#### Scenario: Income row
- **WHEN** an income of 12500000 is displayed in a transaction list
- **THEN** it reads "+Rp12.500.000" in the accent color

#### Scenario: Negative balance
- **WHEN** a balance of −150000 is displayed
- **THEN** it reads "−Rp150.000"
