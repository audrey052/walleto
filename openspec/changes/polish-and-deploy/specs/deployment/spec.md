# Spec Delta

## Purpose
Defines how Walleto runs on a public server: configuration from the environment, secure defaults when debugging is off, served static files, a health check, and a repeatable deploy.

## ADDED Requirements

### Requirement: Configuration from the environment
The application SHALL read its secret key, debug flag, allowed host names, trusted origins, database location and AI settings from environment variables. It SHALL NOT start without a secret key. Without a database location it SHALL use a local file database. Without a debug flag it SHALL run with debugging off.

#### Scenario: Missing secret
- **WHEN** the application starts without a secret key in the environment
- **THEN** it stops with an error naming the missing setting

#### Scenario: Database from a URL
- **WHEN** the environment gives a PostgreSQL database URL
- **THEN** the application stores its data in that database

#### Scenario: Encrypted database connection
- **WHEN** the database URL asks for SSL
- **THEN** the application connects to the database over SSL

#### Scenario: Database woke from idle
- **WHEN** the database closed the application's connection while idle and a visitor then opens a page
- **THEN** the page loads normally on a fresh connection, with no error

#### Scenario: Local default
- **WHEN** no database URL is given
- **THEN** the application uses the local file database, as before

### Requirement: Secure when debugging is off
When debugging is off, the application SHALL accept requests only for its configured host names. It SHALL redirect plain HTTP to HTTPS, mark the session and CSRF cookies as HTTPS-only, and send HSTS. The development style guide page SHALL return 404. The platform's deployment check SHALL report no warnings.

#### Scenario: Unknown host
- **WHEN** a request arrives with a host name that is not configured
- **THEN** it is refused with status 400

#### Scenario: Plain HTTP
- **WHEN** a visitor opens the site over plain HTTP
- **THEN** they are redirected to the same address over HTTPS

#### Scenario: Deployment check
- **WHEN** the deployment check runs with production settings
- **THEN** it reports no issues

### Requirement: Static files in production
With debugging off, the application SHALL serve its own built stylesheet, scripts, fonts and images. Their file names SHALL carry a content fingerprint, so browsers can cache them for a long time and still receive changes after a deploy.

#### Scenario: Styled pages in production
- **WHEN** a visitor opens the sign-in page on the deployed site
- **THEN** the page is styled and its stylesheet address contains a content fingerprint

### Requirement: Health check
The application SHALL answer `GET /healthz` with status 200 and a short plain-text body, without sign-in and without touching user data.

#### Scenario: Platform health check
- **WHEN** the hosting platform requests `/healthz`
- **THEN** it receives status 200 while the application is running

### Requirement: Repeatable deploy
The repository SHALL include one build script and a written deploy guide. The guide SHALL list every service to create, its region, the build and start commands, the health check path and every environment value, with how to get each one. A deploy SHALL build the stylesheet from source, collect the static files and apply database migrations before the new version takes traffic. The repository and the guide SHALL NOT contain any real secret or connection string.

#### Scenario: First deploy from the guide
- **WHEN** the developer follows the guide on fresh Render and Neon accounts
- **THEN** the site comes up with an empty migrated database and a working "Try demo account"

#### Scenario: Later deploy with a new migration
- **WHEN** a commit with a new migration is deployed
- **THEN** the migration is applied before the new version serves requests, and existing data stays

#### Scenario: No secrets in the repository
- **WHEN** the repository and the guide are searched for connection strings and keys
- **THEN** only placeholders are found
