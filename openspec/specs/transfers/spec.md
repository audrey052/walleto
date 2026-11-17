# transfers Specification

## Purpose
Lets a user move money between their own wallets, such as topping up GoPay from BCA, so balances stay correct without the move counting as income or spending.

## Requirements

### Requirement: Transfer between wallets
A signed-in user SHALL be able to record a transfer from one of their active wallets to another of their active wallets, with an amount greater than zero, a date (default today, not in the future) and an optional note. The source and destination SHALL be different. The source wallet's balance SHALL decrease and the destination's SHALL increase by the amount; the total across wallets SHALL stay the same. A toast SHALL say "Transfer recorded."

#### Scenario: Top up an e-wallet
- **WHEN** a user transfers "200.000" from BCA to GoPay
- **THEN** BCA's balance drops by Rp200.000, GoPay's rises by Rp200.000, and the total balance is unchanged

#### Scenario: Same wallet
- **WHEN** the source and destination are the same wallet
- **THEN** the transfer is not saved and the form says to choose two different wallets

#### Scenario: Fewer than two wallets
- **WHEN** a user with only one active wallet opens the transfer form
- **THEN** the form explains that a second wallet is needed and offers to add one

### Requirement: Transfers are not income or expenses
Transfers SHALL NOT count toward income, expenses or net. In the Transactions table they SHALL appear as a neutral row showing "From → To" as the transaction and the wallet, "Transfer" in the Category column, and the amount without a plus or minus sign.

#### Scenario: Transfer in the list
- **WHEN** a transfer of Rp200.000 from BCA to GoPay was made on 12 November
- **THEN** the table shows a "BCA → GoPay" row dated 12 Nov 2026 with Rp200.000, and the month's expenses do not include it

### Requirement: Edit and delete a transfer
A user SHALL be able to edit a transfer's wallets, amount, date and note with the same validation, and delete it after confirming. Toasts SHALL say "Transfer updated." and "Transfer deleted."

#### Scenario: Delete a transfer
- **WHEN** a user deletes the BCA → GoPay transfer and confirms
- **THEN** both wallet balances return to what they were before the transfer

### Requirement: Transfers are private
A user SHALL only see, edit and delete their own transfers, and a transfer SHALL only use the user's own wallets. Requests for another user's transfer SHALL respond as if it did not exist.

#### Scenario: Another user's transfer
- **WHEN** a user requests the edit or delete action for someone else's transfer
- **THEN** a "page not found" response is returned and the transfer is unchanged

### Requirement: A transfer can't overdraw its source
A transfer's amount SHALL NOT be larger than the source wallet's current balance. When editing a transfer that already takes money from the same source, its own amount SHALL count as available. A transfer that is too large SHALL NOT be saved, and the form SHALL say "Not enough in <wallet>. Choose another wallet or a smaller amount." Expenses and income are not affected by this rule.

#### Scenario: Too much
- **WHEN** BCA holds Rp500.000 and a user transfers "600.000" from BCA to GoPay
- **THEN** the transfer is not saved and the form says "Not enough in BCA. Choose another wallet or a smaller amount."

#### Scenario: Exactly the balance
- **WHEN** BCA holds Rp500.000 and a user transfers "500.000" from BCA to GoPay
- **THEN** the transfer is saved and BCA's balance becomes Rp0

#### Scenario: Editing counts the old amount
- **WHEN** BCA holds Rp100.000 after an existing Rp200.000 transfer from BCA, and the user edits that transfer to Rp300.000
- **THEN** the transfer is saved, because Rp300.000 is available (Rp100.000 + Rp200.000)

### Requirement: Transfer preview
The transfer modal SHALL show the source wallet's available balance under From and the destination's current balance under To, a button that swaps the two wallets, and, as the amount is typed, both balances after the transfer with the line "Your total balance stays the same." The submit button SHALL name the amount once one is entered. Without JavaScript the form SHALL still work, without the live preview.

#### Scenario: Live summary
- **WHEN** BCA holds Rp7.842.500, GoPay holds Rp647.500, and the user types "200.000"
- **THEN** the modal shows "BCA after transfer Rp7.642.500", "GoPay after transfer Rp847.500" and a "Transfer Rp200.000" button

#### Scenario: Swap
- **WHEN** the user chooses the swap button with From BCA and To GoPay
- **THEN** From becomes GoPay and To becomes BCA, and the balances shown follow
