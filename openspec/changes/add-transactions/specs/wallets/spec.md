# Spec Delta

## MODIFIED Requirements

### Requirement: Wallets page and total balance
The Wallets page SHALL show, as its main figure, the total balance of the user's active wallets, followed by one card per active wallet in the order they were added. Each card SHALL show a monogram, the wallet name, its type, its balance and a "View activity" link that opens the Transactions page filtered to that wallet. A wallet's balance SHALL equal its starting balance, plus its income, minus its expenses, plus transfers into it, minus transfers out of it, over all dates. A balance MAY be negative and SHALL then be shown with a minus sign. The page SHALL offer a "Transfer" action when the user has at least two active wallets.

#### Scenario: Total across wallets
- **WHEN** a user has active wallets with balances Rp7.842.500, Rp647.500 and Rp485.000
- **THEN** the page shows a total of Rp8.975.000 and three wallet cards

#### Scenario: No wallets yet
- **WHEN** a user with no active wallets opens the Wallets page
- **THEN** the page shows an empty state inviting them to add their first wallet, and no total

#### Scenario: Balance from activity
- **WHEN** BCA started at Rp1.000.000 and has income Rp500.000, expenses Rp200.000, a transfer in of Rp50.000 and a transfer out of Rp300.000
- **THEN** BCA's card shows Rp1.050.000

#### Scenario: Negative balance
- **WHEN** a cash wallet that started at Rp20.000 has expenses of Rp50.000
- **THEN** its card shows −Rp30.000

#### Scenario: View activity
- **WHEN** a user chooses "View activity" on the GoPay card
- **THEN** the Transactions page opens for the current month filtered to GoPay

### Requirement: Archive and restore a wallet
A user SHALL be able to archive a wallet after confirming. An archived wallet SHALL disappear from the wallet cards and from the total, SHALL NOT be offered for new transactions or transfers, and SHALL be listed in a separate "Archived" section, with its balance, from which it can be restored. Its past transactions and transfers SHALL be kept and stay visible on the Transactions page. A wallet SHALL NOT be deletable from the app. Restoring SHALL be refused when an active wallet already uses the same name.

#### Scenario: Archive
- **WHEN** a user archives "OVO" and confirms
- **THEN** the OVO card and its balance leave the total, OVO appears under "Archived", and a toast says "OVO archived."

#### Scenario: Restore
- **WHEN** a user restores an archived "OVO"
- **THEN** OVO is back among the wallet cards and in the total

#### Scenario: Name reused after archiving
- **WHEN** a user archives "OVO", then adds a new wallet named "OVO"
- **THEN** the new wallet is created

#### Scenario: Restore blocked by a name in use
- **WHEN** a user tries to restore an archived "OVO" while an active wallet is also named "OVO"
- **THEN** the archived wallet stays archived and an error toast explains that the name is in use

#### Scenario: History kept
- **WHEN** a user archives a wallet that has transactions
- **THEN** those transactions still appear on the Transactions page under their dates
