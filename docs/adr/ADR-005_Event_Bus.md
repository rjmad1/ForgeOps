# ADR-005: Event Bus for Asynchronous Decoupling

## Context and Problem
Directly coupling state transitions (e.g. starting a service, detecting a service failure, updating configurations) to external systems like metric writers, capability refreshers, audit logs, or notifications makes the codebase complex and highly coupled.

## Decisions
- Introduce a centralized in-memory Event Bus.
- Publish state transitions as discrete domain events (e.g. `ServiceStartedEvent`, `HealthChangedEvent`, `ConfigUpdatedEvent`, `CapabilitiesRefreshedEvent`).
- Allow interested subsystems to register listener/subscriber callbacks to handle events asynchronously or synchronously without direct dependencies.

## Rationale
- **Decoupling**: The Service Registry does not need to know about the Capability Registry or logging sinks. It simply publishes `ServiceStartedEvent` or `HealthChangedEvent`, and the registries respond by updating their local cache or calling discovery.
- **Observability**: Simplifies logging and external dashboard integrations.

## Status
Accepted.
