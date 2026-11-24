# Spec Delta

## MODIFIED Requirements

### Requirement: One month at a time
The Transactions page SHALL show one period at a time, the current month by default, chosen with the period picker (a whole month or a range of days up to today). The selected period SHALL be part of the address.

#### Scenario: Previous month
- **WHEN** a user selects the previous month
- **THEN** the summary and list show October's transactions, and the address includes the month so it can be shared or reloaded

#### Scenario: No future months
- **WHEN** the current month is selected
- **THEN** the month picker offers no next month

#### Scenario: A range of days
- **WHEN** a user picks 10 to 24 November
- **THEN** the summary and list show only entries dated 10 to 24 November, and the address ends with `?from=2026-11-10&to=2026-11-24`

### Requirement: Month summary line
Above the list, a summary line SHALL show how many entries the selected period has after filters, and the period's total income and total expenses, labelled "Income" and "Expenses". Transfers SHALL be counted as entries but excluded from income and expenses.

#### Scenario: Month summary
- **WHEN** November has income Rp12.500.000 and expenses Rp5.847.500, plus a transfer of Rp500.000
- **THEN** the summary shows 3 or more entries, Income +Rp12.500.000 and Expenses Rp5.847.500

#### Scenario: Range summary
- **WHEN** the period is 18 to 24 November and those days have expenses of Rp1.200.000 and no income
- **THEN** the summary shows Income +Rp0 and Expenses Rp1.200.000, and nothing dated before 18 November is counted

### Requirement: Filter and search
On the Transactions page the user SHALL be able to filter by wallet and by category and search descriptions and notes (case-insensitive). Filters SHALL apply within the selected period, update the list and summary without reloading the page, and be reflected in the address together with the period. Filtering by category SHALL hide transfers; filtering by wallet SHALL keep transfers into or out of that wallet.

#### Scenario: Search
- **WHEN** a user types "kopi" in the search box
- **THEN** only the period's transactions whose description or note contains "kopi" (any case) are listed

#### Scenario: Wallet filter includes its transfers
- **WHEN** a user filters by GoPay
- **THEN** GoPay's transactions and the transfers from or to GoPay are listed

#### Scenario: No results
- **WHEN** no transaction matches the filters
- **THEN** an empty state says there are no transactions here and offers to clear the filters

#### Scenario: Filters keep the range
- **WHEN** the period is 10 to 24 November and a user filters by GoPay
- **THEN** the address keeps `from=2026-11-10&to=2026-11-24` and adds the wallet

### Requirement: Pagination
The list SHALL show at most 50 entries per page with links to the other pages. The summary line SHALL always cover the whole period, not only the current page.

#### Scenario: Long month
- **WHEN** a month has 120 entries
- **THEN** the list shows pages 1 to 3, page 2 starts where page 1 ended, and the summary still counts all 120

### Requirement: Export to CSV
The Transactions page SHALL offer "Export CSV", which downloads every entry of the selected period that matches the current filters, across all pages, as a UTF-8 file with the columns Date, Type, Description, Note, Category, Wallet and Amount. The file SHALL be named `walleto-transactions-YYYY-MM.csv` for a whole month and `walleto-transactions-YYYY-MM-DD_YYYY-MM-DD.csv` for another range.

#### Scenario: Export a filtered month
- **WHEN** a user searching "kopi" in November chooses Export CSV
- **THEN** the file contains every November entry matching "kopi", including those beyond the first page

#### Scenario: Export a range
- **WHEN** the period is 10 to 24 November and the user chooses Export CSV
- **THEN** the file is named `walleto-transactions-2026-11-10_2026-11-24.csv` and holds only entries dated 10 to 24 November
