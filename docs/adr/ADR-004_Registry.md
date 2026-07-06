# ADR-004: Service and Capability Registries

## Context and Problem
The system needs to know which plugins are loaded, what local processes are active, and what models or tools are exposed to the developer client at any given moment.

## Decisions
Implement two decoupled registry catalogs:
1. **Service Registry**: Manages in-memory active runtime plugins and persists service-level metadata (ports, binary locations, PIDs, current states) via the repositories.
2. **Capability Registry**: Dynamically stores discovered model types, parameter settings, or tool endpoints across active registered runtimes.

## Rationale
- **Single Source of Truth**: Resolves registry lookup logic dynamically. Client endpoints query these registries instead of hitting local processes directly.
- **Dynamic Updates**: Keeps model lists and process configurations synchronized during discovery.

## Status
Accepted.
