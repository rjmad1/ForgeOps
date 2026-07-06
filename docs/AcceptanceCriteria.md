# Acceptance Criteria: AI Runtime Manager

This document defines the acceptance criteria and definitions of done (DoD) for the AI Runtime Manager implementation.

## Core Acceptance Criteria

### AC-1: Native Windows Service Hosting
- **AC-1.1**: The main application must launch and run as a Windows Service.
- **AC-1.2**: Rebooting the system must automatically restart the service and all registered auto-start dependencies.
- **AC-1.3**: The service must stop gracefully under 10 seconds, killing all child processes without leaving zombie binaries.

### AC-2: Subprocess Management & Recovery
- **AC-2.1**: The Process Manager must capture PIDs for Ollama, LiteLLM, and OpenClaw.
- **AC-2.2**: If a monitored process crashes (e.g. killed via Task Manager), the Health Monitor must flag it as down and trigger an automated restart within 5 seconds.
- **AC-2.3**: Manual start/stop/restart via REST API or CLI must succeed within 3 seconds.

### AC-3: Dynamic Model Discovery
- **AC-3.1**: Adding a model to Ollama must trigger an automatic update in the SQLite `models` table on the next discovery scan (frequency = 30s).
- **AC-3.2**: Model names or configurations must never be hardcoded in python source code.
- **AC-3.3**: The system must successfully query Ollama's local engine and parse response weights and metadata.

### AC-4: Synthesized Configuration Sync
- **AC-4.1**: Starting or adding models must regenerate the LiteLLM `config.yaml` file automatically.
- **AC-4.2**: The generated YAML files must be syntactically valid and loaded without errors by LiteLLM and OpenClaw.

### AC-5: Single Page Dashboard UI
- **AC-5.1**: The dashboard must render correctly on Microsoft Edge and Google Chrome on Windows.
- **AC-5.2**: The UI must display: service status, model listings, active connection counts, average latency, and system hardware loads.
- **AC-5.3**: Actions (Start, Stop, Restart) must trigger immediate state updates in the UI.

---

## Definition of Done (DoD)

A feature branch is ready for merge only when:
1. **Compilation**: All Python code compiles, syntax check passes, and TypeScript client builds without errors.
2. **Tests**: All unit and integration tests pass successfully.
3. **Smoke Check**: Successfully registers, runs, and terminates as a service on a target Windows 11 system.
4. **Documentation**: Code comments updated, API routes added to `Interfaces.md`, and any user configuration detailed.
5. **No Regressions**: Port conflicts and CPU leaks are audited and verified absent.
