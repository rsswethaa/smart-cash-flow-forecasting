# Security and Privacy

## Project status

FlowWise NZ is a portfolio prototype. It is not a production banking application and should not be used to store real banking credentials or regulated financial data.

## Supported version

Security fixes are applied to the current `main` branch.

## Current security boundary

The current application:

- uses local SQLite persistence for demonstration data
- does not connect to bank accounts
- does not request or store online-banking passwords
- does not include production multi-user authentication
- does not claim compliance with New Zealand banking/open-banking regulation
- validates forecast inputs and rejects invalid values in the API path

Because the live demo is a public portfolio environment, users should enter only synthetic or non-sensitive example data.

## Secrets

Do not commit:

- API keys
- database passwords
- cloud credentials
- authentication secrets
- real transaction exports containing personal information

Use environment variables for secrets. See `.env.example` for the expected local configuration shape.

## Production requirements

A production version would require, at minimum:

- authenticated user accounts and secure session handling
- CSRF protection for browser mutations
- PostgreSQL or another production datastore with migrations
- encryption in transit and appropriate protection at rest
- strict tenant isolation
- rate limiting and abuse monitoring
- secure audit logging
- secrets management
- dependency and container scanning
- privacy impact assessment and explicit retention/deletion rules
- consent-based bank-data integration rather than credential collection
- regulatory/legal review before presenting outputs as financial advice

## Uploaded or imported financial data

If transaction import is added, the default design should minimise retained raw data, document retention clearly, and allow deletion. Sensitive financial information should never be included in repository fixtures or GitHub issues.

## Reporting a vulnerability

Please avoid publishing exploitable details in a public issue. Contact the repository owner privately through the contact information on the GitHub profile, then provide reproduction steps and the affected version.
