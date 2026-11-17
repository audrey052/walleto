# transactions Specification

## Purpose
Lets a user record every income and expense against a wallet and a category, and review them month by month to see where their money went.

## Requirements

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

### Requirement: One month at a time
The Transactions page SHALL show one month at a time, the current month by default, with a month picker that moves to the previous and next month. It SHALL NOT move beyond the current month, and the selected month SHALL be part of the address.

#### Scenario: Previous month
- **WHEN** a user selects the previous month
- **THEN** the summary and list show October's transactions, and the address includes the month so it can be shared or reloaded

#### Scenario: No future months
- **WHEN** the current month is selected
- **THEN** the month picker offers no next month

### Requirement: Month summary line
Above the list, a summary line SHALL show how many entries the selected month has after filters, and the month's total income and total expenses, labelled "Income" and "Expenses". Transfers SHALL be counted as entries but excluded from income and expenses.

#### Scenario: Month summary
- **WHEN** November has income Rp12.500.000 and expenses Rp5.847.500, plus a transfer of Rp500.000
- **THEN** the summary shows 3 or more entries, Income +Rp12.500.000 and Expenses Rp5.847.500

### Requirement: Transactions table
The month's transactions and transfers SHALL be listed newest first in a table with the columns Transaction (description and note), Category, Wallet, Date and Amount. Choosing a row SHALL open it for editing. On narrow screens the table SHALL scroll sideways instead of squeezing its columns.

#### Scenario: Table rows
- **WHEN** 14 November has expenses GoFood Rp67.500 and Grab Rp32.000
- **THEN** both appear as rows with their category, wallet, the date "14 Nov 2026" and −Rp67.500 and −Rp32.000, above any older rows

#### Scenario: Phone width
- **WHEN** the page is shown 390 pixels wide
- **THEN** the table keeps its columns and can be scrolled sideways, and the page itself does not scroll sideways

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
- **THEN** an empty state says there are no transactions here and offers to clear the filters

### Requirement: Pagination
The list SHALL show at most 50 entries per page with links to the other pages. The summary line SHALL always cover the whole month, not only the current page.

#### Scenario: Long month
- **WHEN** a month has 120 entries
- **THEN** the list shows pages 1 to 3, page 2 starts where page 1 ended, and the summary still counts all 120

### Requirement: Export to CSV
The Transactions page SHALL offer "Export CSV", which downloads every entry of the selected month that matches the current filters, across all pages, as a UTF-8 file named `walleto-transactions-YYYY-MM.csv` with the columns Date, Type, Description, Note, Category, Wallet and Amount.

#### Scenario: Export a filtered month
- **WHEN** a user searching "kopi" in November chooses Export CSV
- **THEN** the file contains every November entry matching "kopi", including those beyond the first page

### Requirement: CSV amounts and transfers
In the export, expenses SHALL have negative amounts and income positive ones. A transfer SHALL appear with type "Transfer", "From → To" as both description and wallet, and an unsigned amount.

#### Scenario: Signed amounts
- **WHEN** November has a GoFood expense of Rp67.500 and a salary of Rp12.500.000
- **THEN** the export lists them with amounts -67500 and 12500000

### Requirement: Safe CSV text
Text that a spreadsheet would read as a formula SHALL be exported so that it is shown as text.

#### Scenario: Formula-looking text
- **WHEN** a transaction's description starts with "="
- **THEN** the exported description is prefixed so the spreadsheet shows it as text

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
