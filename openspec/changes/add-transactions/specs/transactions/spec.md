# Spec Delta

## Purpose

Lets a user record every income and expense against a wallet and a category, and review them month by month to see where their money went.

## ADDED Requirements

### Requirement: Record a transaction
A signed-in user SHALL be able to add a transaction with a description (1 to 80 characters), an amount greater than zero, a date, a category, one of their active wallets, and an optional note (up to 120 characters). Whether it is income or an expense SHALL follow from the category chosen. The date SHALL default to today in Jakarta time and SHALL NOT be in the future. After saving, a toast SHALL say "Transaction added."

#### Scenario: Add an expense
- **WHEN** a user adds "GoFood" for "67.500" in Food & drinks from GoPay today
- **THEN** the transaction appears under today on the Transactions page as −Rp67.500, and GoPay's balance drops by Rp67.500

#### Scenario: Add income
- **WHEN** a user adds "November salary" for "12.500.000" in Salary to BCA
- **THEN** it appears as +Rp12.500.000 in the accent color and BCA's balance rises by that amount

#### Scenario: Zero amount
- **WHEN** the amount is 0 or empty
- **THEN** the transaction is not saved and the form says the amount must be greater than 0

#### Scenario: Future date
- **WHEN** the date is after today in Jakarta time
- **THEN** the transaction is not saved and the form says the date can't be in the future

#### Scenario: Archived wallet
- **WHEN** a user opens the add form
- **THEN** only their active wallets can be chosen

### Requirement: Monthly transactions page
The Transactions page SHALL show one month at a time, the current month by default, with links to the previous and next month (no next link beyond the current month). The page SHALL show the month's total income, total expenses and net (income minus expenses), excluding transfers. Below it, the month's transactions and transfers SHALL be listed newest day first, grouped by day; each day SHALL show its date and the net of that day's income and expenses.

#### Scenario: Month summary
- **WHEN** November has income Rp12.500.000 and expenses Rp5.847.500, plus a transfer of Rp500.000
- **THEN** the summary shows income Rp12.500.000, expenses Rp5.847.500 and net Rp6.652.500

#### Scenario: Day groups
- **WHEN** 14 November has expenses of Rp67.500 and Rp32.000
- **THEN** the list shows a "Saturday, 14 Nov" group with subtotal −Rp99.500 above those two rows

#### Scenario: Previous month
- **WHEN** a user selects the previous month
- **THEN** the summary and list show October's transactions, and the address includes the month so it can be shared or reloaded

### Requirement: Filter and search
On the Transactions page the user SHALL be able to filter by wallet and by category and search descriptions and notes (case-insensitive). Filters SHALL apply within the selected month, update the list and summary without reloading the page, and be reflected in the address. Filtering by category SHALL hide transfers; filtering by wallet SHALL keep transfers into or out of that wallet.

#### Scenario: Search
- **WHEN** a user types "kopi" in the search box
- **THEN** only this month's transactions whose description or note contains "kopi" (any case) are listed

#### Scenario: Wallet filter includes its transfers
- **WHEN** a user filters by GoPay
- **THEN** GoPay's transactions and the transfers from or to GoPay are listed

#### Scenario: No results
- **WHEN** no transaction matches the filters
- **THEN** an empty state says nothing matches and offers to clear the filters

### Requirement: Pagination
The list SHALL show at most 50 entries per page with links to the other pages. A day's subtotal SHALL always cover the whole day, even when the day's entries span two pages.

#### Scenario: Long month
- **WHEN** a month has 120 entries
- **THEN** the list shows pages 1 to 3, and page 2 starts where page 1 ended

### Requirement: Edit and delete a transaction
A user SHALL be able to open a transaction to change any of its fields, with the same validation as adding it, and to delete it after confirming. Editing a transaction that uses an archived wallet SHALL keep that wallet available for that transaction. Toasts SHALL say "Transaction updated." and "Transaction deleted."

#### Scenario: Edit amount
- **WHEN** a user changes a GoFood expense from Rp67.500 to Rp72.500
- **THEN** the row and the wallet balance reflect Rp72.500

#### Scenario: Delete
- **WHEN** a user deletes a transaction and confirms
- **THEN** it disappears from the list and the wallet balance no longer includes it

### Requirement: Transactions are private
A user SHALL only see, edit and delete their own transactions. Requests for another user's transaction SHALL respond as if it did not exist, and a transaction SHALL NOT be saved against another user's wallet or category.

#### Scenario: Another user's transaction
- **WHEN** a user requests the edit or delete action for a transaction owned by someone else
- **THEN** a "page not found" response is returned and the transaction is unchanged

#### Scenario: Another user's wallet in the form
- **WHEN** a submitted form names a wallet that belongs to someone else
- **THEN** the form rejects it as an invalid choice
