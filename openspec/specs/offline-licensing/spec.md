# offline-licensing Specification

## Purpose
TBD - created by archiving change add-electron-desktop-app-and-offline-licensing. Update Purpose after archive.
## Requirements
### Requirement: Provide a machine code for offline activation
The system SHALL expose a stable, privacy-preserving machine code (hardware fingerprint hash) that can be used for offline activation.

#### Scenario: User reads machine code from the app
- **WHEN** the user opens the “授权/激活” panel
- **THEN** the UI SHALL display the machine code
- **AND** the machine code SHALL be usable to generate a license externally (offline)

### Requirement: Accept and validate offline license codes
The system SHALL accept a user-provided offline license code and validate it locally without requiring network access.

The license SHALL be machine-bound by including the machine code (or derived binding) and a cryptographic signature.

#### Scenario: Activate with a valid license code
- **GIVEN** the machine code matches the license binding
- **AND** the license signature is valid
- **WHEN** the user submits the license code
- **THEN** the system SHALL store the license locally
- **AND** the system SHALL report an “authorized” status

#### Scenario: Reject an invalid or mismatched license
- **GIVEN** a license code is invalid, expired, or bound to a different machine
- **WHEN** the user submits the license code
- **THEN** the system SHALL reject activation with an actionable error

### Requirement: Enforce licensing at the API boundary
The system SHALL enforce licensing at the backend API boundary so that unlicensed clients cannot use LLM-backed features or data management endpoints.

#### Scenario: Unlicensed API calls are rejected
- **GIVEN** no valid license is stored
- **WHEN** the client calls any `/api/*` endpoint (except `/api/license/*`)
- **THEN** the API SHALL return 403 with a clear error payload

#### Scenario: Licensed API calls proceed normally
- **GIVEN** a valid license is stored
- **WHEN** the client calls `/api/*` endpoints
- **THEN** the API SHALL proceed as normal

### Requirement: Provide a local license generator tool (operator-only)
The project SHALL provide an operator-only tool to generate license codes from a machine code without requiring network access.

#### Scenario: Generate a license code offline
- **GIVEN** the operator has the signing private key (kept outside the repo)
- **WHEN** the operator runs the license generator with a machine code and optional expiry
- **THEN** the tool SHALL output a license code that the app can validate offline

