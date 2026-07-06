# ADR-002: SQLite Persistence and Repository Abstractions

## Context and Problem
The control plane needs a persistent data store for service parameters, state values, configuration files, and metrics history. It must run locally on Windows 11 without requiring database servers (like PostgreSQL or MySQL). At the same time, the core business domain logic must remain independent of specific SQLite drivers or schemas to maximize testability.

## Decisions
- Use SQLite (via Python's standard `sqlite3` driver) as the local SQL storage mechanism.
- Implement the Repository Pattern. All SQL statements, rows mapping, and connection handlings are strictly encapsulated inside repository implementations, hidden from the Domain Layer.

## Rationale
- **Zero-Configuration**: SQLite runs as a single local file, suited for desktop background services.
- **Independence**: The repository interfaces (`ServiceRepository`, `CapabilityRepository`, `SystemConfigRepository`) decouple SQLite persistence logic from domain structures, allowing standard in-memory mock repositories to be used in unit tests.

## Status
Accepted.
