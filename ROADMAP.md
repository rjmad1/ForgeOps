# Roadmap: AI Runtime Manager

This roadmap details the sequential release stages for the AI Runtime Manager platform.

```
Phase 0 ──> Phase 1 ──> Phase 2 ──> Phase 3 ──> Phase 4 ──> Phase 5
(Docs &     (Core       (Plugins &  (REST API &  (Frontend   (Operations
 Specs)     Services)    Configs)    Metrics)    Dashboard)   & Testing)
```

## Chronological Release Plan

### Phase 0: Specification & Architecture (Current)
- [x] Create project documentation (`docs/*.md`).
- [x] Design technical contracts, database schemas, and folder layouts.
- [x] Design the prioritized backlog based on dependency order.

### Phase 1: Core Service Orchestrator
- [x] Initialize Python virtual environment and SQLite database schemas.
- [x] Implement `ProcessManager` for Windows subprocess execution, tracking, and clean signals.
- [x] Create Python CLI tool and Windows Service host configuration (`win32service`).

### Phase 2: Configuration & Plugin Engine
- [x] Implement base `RuntimePlugin` class and directory loader.
- [x] Build the `OllamaPlugin` (auto-discovery of models via local API, process management).
- [x] Build the `LiteLLMPlugin` (dynamic config generation, routing config generation).
- [x] Build the `OpenClawPlugin` and `MCPPlugin` for service hosting.

### Phase 3: REST API & Metrics Monitoring
- [x] Establish FastAPI app with REST endpoints matching `Interfaces.md`.
- [x] Build the `HealthMonitor` module executing HTTP/TCP checks and logging history.
- [x] Create the `HardwareMetrics` poller using `psutil` and GPU utilities (e.g. `nvidia-smi` parser).

### Phase 4: Single-Page React Dashboard
- [x] Set up Vite + React + TypeScript web client.
- [x] Implement layout showing: Installed services, running services, loaded models, GPU/VRAM/CPU metrics.
- [x] Add control panels (Start, Stop, Restart buttons) calling the REST API.
- [x] Add real-time log viewers and latency trackers.

### Phase 5: Diagnostics, Operations & Validation
- [x] Implement backup/restore commands for configs and database.
- [x] Implement performance benchmarking tool (measuring TTFT, tokens-per-second, and queue latency).
- [x] Deliver full test suite (Smoke, Unit, Integration, Health check).
