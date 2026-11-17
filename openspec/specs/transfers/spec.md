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
