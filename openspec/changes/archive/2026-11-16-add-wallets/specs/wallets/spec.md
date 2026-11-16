# Spec Delta

## Purpose

Lets a user record the places their money is kept (cash, bank accounts, e-wallets), see what each holds and the total across all of them, and retire a wallet without losing its history.

## ADDED Requirements

### Requirement: Create a wallet
A signed-in user SHALL be able to add a wallet with a name (1 to 40 characters), a type (Cash, Bank account or E-wallet) and a starting balance of zero or more. The name SHALL be unique among the user's active wallets, compared without regard to letter case. A new wallet SHALL appear on the Wallets page immediately, with a confirmation toast.

#### Scenario: Add a wallet
- **WHEN** a user adds a wallet named "BCA" of type Bank account with starting balance "7.842.500"
- **THEN** a "BCA" card showing Rp7.842.500 appears on the Wallets page and a toast says "Wallet added."

#### Scenario: Duplicate name
- **WHEN** a user who already has an active wallet "GoPay" adds another wallet named "gopay"
- **THEN** no wallet is created and the form shows "You already have a wallet with this name." next to the name

#### Scenario: Missing name
- **WHEN** the name is empty or only spaces
- **THEN** no wallet is created and the form asks for a name

#### Scenario: Negative starting balance
- **WHEN** the starting balance is below zero
- **THEN** no wallet is created and the form says the balance cannot be negative

### Requirement: Rupiah amount input
Amount fields SHALL accept whole Rupiah written with dots, commas or spaces as thousands separators and an optional "Rp" prefix. Text that is not a whole number of Rupiah SHALL be rejected with an explanation. An empty starting balance SHALL mean zero.

#### Scenario: Indonesian separators
- **WHEN** the starting balance is entered as "2.500.000"
- **THEN** it is saved as 2500000

#### Scenario: Prefix and commas
- **WHEN** the starting balance is entered as "Rp 1,250,000"
- **THEN** it is saved as 1250000

#### Scenario: Not a number
- **WHEN** the starting balance is entered as "dua juta"
- **THEN** the wallet is not saved and the form says "Enter an amount in Rupiah, for example 2.500.000."

#### Scenario: Empty balance
- **WHEN** the starting balance is left empty
- **THEN** the wallet is saved with a balance of Rp0

### Requirement: Wallets page and total balance
The Wallets page SHALL show, as its main figure, the total balance of the user's active wallets, followed by one card per active wallet in the order they were added. Each card SHALL show a monogram, the wallet name, its type and its balance. Until transactions exist, a wallet's balance SHALL equal its starting balance.

#### Scenario: Total across wallets
- **WHEN** a user has active wallets with balances Rp7.842.500, Rp647.500 and Rp485.000
- **THEN** the page shows a total of Rp8.975.000 and three wallet cards

#### Scenario: No wallets yet
- **WHEN** a user with no active wallets opens the Wallets page
- **THEN** the page shows an empty state inviting them to add their first wallet, and no total

### Requirement: Wallet monogram
Each wallet SHALL be shown with a short monogram derived from its name: the whole name in capitals when it is a single word of up to four letters ("BCA", "OVO"), the initials of the first two words when the name has several words ("Bank Jago" → "BJ"), and otherwise the first two letters ("GoPay" → "Go"). Cash wallets SHALL use "Rp".

#### Scenario: Monograms
- **WHEN** wallets named "BCA" (bank), "Bank Jago" (bank), "GoPay" (e-wallet) and "Dompet" (cash) are shown
- **THEN** their monograms are "BCA", "BJ", "Go" and "Rp"

### Requirement: Edit a wallet
A user SHALL be able to change a wallet's name, type and starting balance. The same validation as creating a wallet SHALL apply, ignoring the wallet being edited when checking for duplicate names.

#### Scenario: Rename a wallet
- **WHEN** a user renames "BCA" to "BCA Tahapan"
- **THEN** the card shows "BCA Tahapan" and a toast says "Wallet updated."

### Requirement: Archive and restore a wallet
A user SHALL be able to archive a wallet after confirming. An archived wallet SHALL disappear from the wallet cards and from the total, and SHALL be listed in a separate "Archived" section from which it can be restored. A wallet SHALL NOT be deletable from the app. Restoring SHALL be refused when an active wallet already uses the same name.

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

### Requirement: Wallets are private
A user SHALL only see and change their own wallets. Opening, editing, archiving or restoring another user's wallet, including by changing the ID in an address, SHALL respond as if the wallet did not exist.

#### Scenario: Another user's wallet
- **WHEN** a user requests the edit form or the archive action for a wallet owned by someone else
- **THEN** a "page not found" response is returned and the wallet is unchanged

### Requirement: Forms open in place
Adding, editing and archiving SHALL open in a modal without leaving the Wallets page. When a form has errors, the modal SHALL stay open and show them. The same forms SHALL also work as full pages when opened directly.

#### Scenario: Error keeps the modal open
- **WHEN** a user submits the add-wallet modal with an empty name
- **THEN** the modal stays open with the entered values and the error message
