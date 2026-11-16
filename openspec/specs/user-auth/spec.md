# user-auth Specification

## Purpose
Lets a person create a Walleto account, sign in and out with email and password, and ensures that only signed-in users can reach their finance pages.

## Requirements

### Requirement: Registration with email and password
The system SHALL let a visitor create an account with a full name, an email address and a password entered twice. The email address SHALL be unique, compared without regard to letter case. The password SHALL pass the standard password strength checks (minimum length, not too common, not entirely numeric, not too similar to the name or email). After successful registration the user SHALL be signed in and taken to the home page.

#### Scenario: Successful registration
- **WHEN** a visitor submits a name, a new email address and a strong password typed the same way twice
- **THEN** an account is created, the user is signed in, and the home page is shown

#### Scenario: Email already registered
- **WHEN** a visitor registers with an email address that already belongs to an account, in any letter case
- **THEN** no account is created and the form shows "An account with this email already exists." next to the email field

#### Scenario: Passwords do not match
- **WHEN** the two password fields differ
- **THEN** no account is created and the form shows an error next to the second password field, keeping the name and email that were entered

#### Scenario: Weak password
- **WHEN** the password is shorter than the minimum length or is a common password
- **THEN** no account is created and the form explains which rule the password failed

### Requirement: Sign in with email and password
The system SHALL let a registered user sign in with their email address and password. A failed sign-in SHALL show one generic error that does not reveal whether the email address exists.

#### Scenario: Valid credentials
- **WHEN** a user submits a registered email address (in any letter case) and the correct password
- **THEN** the user is signed in and taken to the home page

#### Scenario: Invalid credentials
- **WHEN** a user submits an unknown email address, or a known email address with a wrong password
- **THEN** the user is not signed in and the form shows "Email or password is incorrect."

### Requirement: Sign out
The system SHALL let a signed-in user sign out from the profile menu. Signing out SHALL only happen through a form submission, not by opening a link, so that another site cannot sign the user out.

#### Scenario: Sign out from the profile menu
- **WHEN** a signed-in user chooses "Sign out" in the profile menu
- **THEN** the session ends and the sign-in page is shown

#### Scenario: Sign-out link opened directly
- **WHEN** someone opens the sign-out address with a plain page request instead of the form
- **THEN** the user stays signed in

### Requirement: Pages require sign-in
Every page except sign-in and registration SHALL require a signed-in user. A visitor who is not signed in SHALL be sent to the sign-in page and, after signing in, returned to the page they originally asked for.

#### Scenario: Visitor opens a protected page
- **WHEN** a visitor who is not signed in opens the Budget page
- **THEN** the sign-in page is shown, and after a successful sign-in the Budget page is shown

#### Scenario: Return address points to another site
- **WHEN** the return address passed to the sign-in page points to a different website
- **THEN** after signing in the user is taken to the home page instead

### Requirement: Signed-in users skip the sign-in pages
A user who is already signed in SHALL NOT see the sign-in or registration forms.

#### Scenario: Signed-in user opens the sign-in page
- **WHEN** a signed-in user opens the sign-in or registration page
- **THEN** the home page is shown instead
