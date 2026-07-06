# ADR-006: Health and Workflow (Orchestration) Engines

## Context and Problem
Earlier versions of the control plane delegated state transitions and service startup/shutdown steps entirely to individual plugins, which led to:
- Inconsistent and hardcoded status logic across plugins.
- Inability to safely recover, configure, or roll back if a process failed to initialize properly.

## Decisions
1. **Centralized Health Engine**: Plugins return raw health check checks (e.g. PID status, port reachability status). A centralized `HealthEngine` evaluates these checks against core business rules to assign states.
2. **Workflow Engine**: Multi-step service lifecycle tasks (startup checks, pre-flight validations, binary path configuration, post-launch port polling, fallback procedures, and model discovery) are managed via explicit step-based `Workflow` states.

## Rationale
- **Consistency**: Health state boundaries (e.g. `UPDATING`, `DEGRADED`, `ERROR`) are defined in one place rather than duplicated.
- **Resiliency**: Steps during startup are strictly verified. If a service fails to initialize (e.g. port already bound), the startup workflow rolls back, terminates the process, and reports a clean state.

## Status
Accepted.
