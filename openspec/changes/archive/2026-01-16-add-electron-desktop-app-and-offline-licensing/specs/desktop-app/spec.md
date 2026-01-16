# desktop-app (delta)

## ADDED Requirements

### Requirement: Deliver as a macOS/Windows desktop app
The system SHALL be deliverable as a desktop application for macOS and Windows using Electron.

#### Scenario: Launch desktop app starts local API and shows UI
- **GIVEN** the user has installed the desktop app
- **WHEN** the user launches the app
- **THEN** the app SHALL start a local API sidecar bound to localhost
- **AND** the app SHALL open the IDE UI connected to that local API
- **AND** the app SHALL stop the sidecar when the app quits

### Requirement: Desktop app uses an embedded database by default
The desktop app SHALL not require the user to install Postgres or Docker and SHALL use an embedded database by default.

#### Scenario: Data persists in a user data directory
- **GIVEN** the user creates Briefs/Snapshots and generates content
- **WHEN** the user closes and reopens the desktop app
- **THEN** the previously created content SHALL still be available
- **AND** the persisted data SHALL be stored under the OS user data directory (per-user)

### Requirement: Desktop startup initializes database schema automatically
The system SHALL initialize or upgrade the embedded database schema automatically on desktop startup.

#### Scenario: First run creates schema
- **GIVEN** this is the first run on a machine
- **WHEN** the API sidecar starts
- **THEN** it SHALL create the database file and required schema without manual commands

#### Scenario: Upgrade after app update
- **GIVEN** the user updates to a newer desktop version
- **WHEN** the API sidecar starts
- **THEN** it SHALL upgrade the schema to the latest version (or fail with an actionable error)
