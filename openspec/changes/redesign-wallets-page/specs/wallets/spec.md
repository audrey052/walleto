# Spec Delta

## MODIFIED Requirements

### Requirement: Create a wallet
A signed-in user SHALL be able to add a wallet with a name (1 to 40 characters), a type (Cash, Bank account or E-wallet) and a starting balance of zero or more. The name SHALL be unique among the user's active wallets, compared without regard to letter case. A new wallet SHALL appear on the Wallets page immediately, with a confirmation toast.

#### Scenario: Add a wallet
- **WHEN** a user adds a wallet named "BCA" of type Bank account with starting balance "7.842.500"
- **THEN** a "BCA" row showing Rp7.842.500 appears in the wallets table and a toast says "Wallet added."

#### Scenario: Duplicate name
- **WHEN** a user who already has an active wallet "GoPay" adds another wallet named "gopay"
- **THEN** no wallet is created and the form shows "You already have a wallet with this name." next to the name

#### Scenario: Missing name
- **WHEN** the name is empty or only spaces
- **THEN** no wallet is created and the form asks for a name

#### Scenario: Negative starting balance
- **WHEN** the starting balance is below zero
- **THEN** no wallet is created and the form says the balance cannot be negative

#### Scenario: Live preview
- **WHEN** a user types "Mandiri" as the name and picks Bank account in the add-wallet modal
- **THEN** the preview card at the top of the modal shows "Mandiri" and "Bank account" before saving

### Requirement: Wallets page and total balance
The Wallets page SHALL show a balance panel with the total balance of the user's active wallets, the number of active wallets and today's date, followed by a "Your wallets" table with one row per active wallet in the order they were added. Each row SHALL show the wallet name, its type, its 30-day balance trend and its balance, and SHALL open the Transactions page filtered to that wallet when chosen. A wallet's balance SHALL equal its starting balance, plus its income, minus its expenses, plus transfers into it, minus transfers out of it, over all dates. A negative balance SHALL be shown with a minus sign.

#### Scenario: Total across wallets
- **WHEN** a user has active wallets with balances Rp7.842.500, Rp647.500 and Rp485.000
- **THEN** the panel shows a total of Rp8.975.000, "Across 3 wallets", and the table has three rows

#### Scenario: No wallets yet
- **WHEN** a user with no active wallets opens the Wallets page
- **THEN** the page shows an empty state inviting them to add their first wallet, and no panel or table

#### Scenario: Balance from activity
- **WHEN** BCA started at Rp1.000.000 and has income Rp500.000, expenses Rp200.000, a transfer in of Rp50.000 and a transfer out of Rp300.000
- **THEN** BCA's row shows Rp1.050.000

#### Scenario: Negative balance
- **WHEN** a cash wallet that started at Rp20.000 has expenses of Rp50.000
- **THEN** its row shows −Rp30.000

#### Scenario: View activity
- **WHEN** a user chooses the GoPay row
- **THEN** the Transactions page opens for the current month filtered to GoPay

### Requirement: Edit a wallet
A user SHALL be able to change a wallet's name, type and starting balance. The same validation as creating a wallet SHALL apply, ignoring the wallet being edited when checking for duplicate names.

#### Scenario: Rename a wallet
- **WHEN** a user renames "BCA" to "BCA Tahapan"
- **THEN** the row shows "BCA Tahapan" and a toast says "Wallet updated."

### Requirement: Archive and restore a wallet
A user SHALL be able to archive a wallet after confirming. An archived wallet SHALL disappear from the wallets table, the total and the type breakdown, SHALL NOT be offered for new transactions or transfers, and SHALL be listed in a separate "Archived" section, with its balance, from which it can be restored. Its past transactions and transfers SHALL be kept and stay visible on the Transactions page. A wallet SHALL NOT be deletable from the app. Restoring SHALL be refused when an active wallet already uses the same name.

#### Scenario: Archive
- **WHEN** a user archives "OVO" and confirms
- **THEN** the OVO row and its balance leave the table, the total and the E-wallets figure, OVO appears under "Archived", and a toast says "OVO archived."

#### Scenario: Restore
- **WHEN** a user restores an archived "OVO"
- **THEN** OVO is back in the wallets table and in the total

#### Scenario: Name reused after archiving
- **WHEN** a user archives "OVO", then adds a new wallet named "OVO"
- **THEN** the new wallet is created

#### Scenario: Restore blocked by a name in use
- **WHEN** a user tries to restore an archived "OVO" while an active wallet is also named "OVO"
- **THEN** the archived wallet stays archived and an error toast explains that the name is in use

#### Scenario: History kept
- **WHEN** a user archives a wallet that has transactions
- **THEN** those transactions still appear on the Transactions page under their dates

## ADDED Requirements

### Requirement: Balance by wallet type
Next to the total, the balance panel SHALL show the summed balance of the user's active wallets for each type: "Bank accounts", "E-wallets" and "Cash". A type with no wallets SHALL show Rp0. The three figures SHALL add up to the total.

#### Scenario: Breakdown
- **WHEN** a user has BCA (bank) Rp7.842.500, Jago (bank) Rp3.275.000, GoPay (e-wallet) Rp647.500 and no cash wallet
- **THEN** the panel shows Bank accounts Rp11.117.500, E-wallets Rp647.500 and Cash Rp0

### Requirement: 30-day balance trend
Each row SHALL show a small line of the wallet's balance at the end of each of the last 30 days, ending today in Jakarta time. The balance at the end of a day SHALL count every transaction and transfer dated on or before that day. The table heading SHALL show the date range, for example "19 Oct–17 Nov 2026".

#### Scenario: Trend follows activity
- **WHEN** GoPay ended 16 November at Rp400.000 and a Rp67.500 expense is dated 17 November
- **THEN** the last two points of GoPay's trend are Rp400.000 and Rp332.500

#### Scenario: No activity
- **WHEN** a wallet has no transactions or transfers in the last 30 days
- **THEN** its trend is a flat line at its current balance

### Requirement: Wallet row actions
Each wallet row SHALL offer edit and archive actions as icons that appear when the row is hovered or has keyboard focus, and are always visible on screens narrower than 768 pixels. Choosing an action SHALL open its modal and SHALL NOT open the wallet's activity.

#### Scenario: Edit from a row
- **WHEN** a user hovers the BCA row and chooses the edit icon
- **THEN** the edit modal for BCA opens and the Transactions page is not opened

### Requirement: Recent transfers on Wallets
When the user has transfers, the Wallets page SHALL list the three most recent ones (by date, then creation), each with "From → To", its note (or "Between your wallets") and date, and its amount. Choosing one SHALL open its edit modal. The page SHALL also show a note that transfers move money without changing the total, with a "Move money" action that opens the transfer modal when the user has at least two active wallets.

#### Scenario: Three most recent
- **WHEN** a user has five transfers
- **THEN** the Recent transfers list shows the three latest, newest first

#### Scenario: No transfers
- **WHEN** a user has never made a transfer
- **THEN** no Recent transfers list is shown

## REMOVED Requirements

### Requirement: Wallet monogram
**Reason**: The Figma Wallets table identifies each wallet by its name only; the monogram tile belonged to the old card layout.
**Migration**: None. The `monogram` property is removed; wallet colors stay and are still used by the Transactions page.
