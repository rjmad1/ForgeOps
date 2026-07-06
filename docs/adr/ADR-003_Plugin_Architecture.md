# ADR-003: Extensible Runtime Plugin Contract

## Context and Problem
The control plane orchestrates multiple heterogeneous local runtimes (Ollama, LiteLLM, OpenClaw, MCP servers). Integrating each runtime with ad-hoc logic results in tight coupling and makes onboarding future engines complex and error-prone.

## Decisions
- Establish a strict `RuntimePlugin` domain contract interface.
- Express all runtime-specific functionalities (starting, stopping, metrics pulling, raw health telemetries, declarative configuration generation) via this single plugin contract.

## Rationale
- **Extensibility**: Adding support for a new engine (e.g. vLLM or llama.cpp) requires zero modifications to the core control plane. Instead, developer only implements a new plugin class adhering to `RuntimePlugin`.
- **Decoupling**: Central API gateways and engines interface only with the contract, shielding them from the specific command-line arguments, environment configurations, and rest endpoints of the underlying runtimes.

## Status
Accepted.
