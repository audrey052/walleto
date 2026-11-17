# Spec Delta

## ADDED Requirements

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
