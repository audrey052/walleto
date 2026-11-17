# demo-account Specification

## Purpose
Lets a visitor, such as a recruiter, try Walleto immediately with realistic data instead of registering and entering transactions first.

## Requirements

### Requirement: Demo data
A management command SHALL create or reset one demo user with five wallets (BCA, GoPay, OVO, Bank Jago, Cash), monthly salary, realistic everyday expenses at Indonesian merchants with irregular amounts, and wallet top-up transfers, covering the current month up to today and the two months before it. Running the command again SHALL replace the demo user's data with a fresh set and leave every other user untouched. The data SHALL be the same each time for the same date.

#### Scenario: Fresh demo data
- **WHEN** the command runs on 16 November 2026
- **THEN** the demo user has five wallets, salary on 1 September, 1 October and 1 November, expenses on most days from 1 September to 16 November, and no transaction dated after 16 November

#### Scenario: Reset leaves others alone
- **WHEN** the command runs a second time
- **THEN** the demo user's previous transactions are replaced, and other users' data is unchanged

#### Scenario: Balances stay positive
- **WHEN** the demo data has been created
- **THEN** every demo wallet ends with a balance of zero or more

### Requirement: Try the demo account
The sign-in page SHALL offer "Try demo account". Choosing it SHALL sign the visitor in as the demo user (creating the demo data first if the demo user does not exist) and open the Dashboard with a toast saying they are using the demo account. The action SHALL only work through a form submission.

#### Scenario: Visitor tries the demo
- **WHEN** a visitor on the sign-in page chooses "Try demo account"
- **THEN** they are signed in as the demo user and see a toast "You're using the demo account."

#### Scenario: Demo user missing
- **WHEN** the demo user does not exist yet and a visitor chooses "Try demo account"
- **THEN** the demo user and its data are created and the visitor is signed in
