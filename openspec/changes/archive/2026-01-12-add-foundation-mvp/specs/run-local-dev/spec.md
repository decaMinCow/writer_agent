## ADDED Requirements

### Requirement: Local development environment
The system SHALL provide a local development environment that can be started with `docker-compose` to run required infrastructure dependencies for development.

#### Scenario: Start Postgres + pgvector for development
- **WHEN** a developer runs `docker compose up -d` from the repository root (or documented directory)
- **THEN** Postgres SHALL start successfully with the pgvector extension available
- **AND** the connection details SHALL be documented via an example env file and/or README instructions

