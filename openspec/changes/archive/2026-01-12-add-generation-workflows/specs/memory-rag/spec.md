## ADDED Requirements

### Requirement: Store and retrieve story memory via embeddings
The system SHALL store committed story text as retrievable memory chunks and support similarity retrieval for generation steps.

#### Scenario: Index committed text
- **WHEN** an artifact version is committed
- **THEN** the system SHALL store one or more memory chunks linked to that artifact version

#### Scenario: Retrieve relevant evidence for a step
- **WHEN** a generation step requests evidence using a query
- **THEN** the system SHALL return the top-k most relevant memory chunks for use as constraints

