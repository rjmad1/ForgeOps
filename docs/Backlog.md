# Implementation Backlog: AI Runtime Manager

This backlog contains the prioritized tasks for building the AI Runtime Manager. Tasks are ordered strictly by dependency.

```
┌────────────────────────┐
│  Phase 1: Core Infra   │  (BL-101 to BL-105)
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│   Phase 2: Plugins     │  (BL-201 to BL-205)
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│    Phase 3: APIs       │  (BL-301 to BL-303)
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│   Phase 4: Dashboard   │  (BL-401 to BL-403)
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│  Phase 5: Operations   │  (BL-501 to BL-503)
└────────────────────────┘
```

---

## Phase 1: Core Infrastructure

### BL-101: Project Skeleton & Dependency Management
- **Description**: Set up the `pyproject.toml`, `requirements.txt`, and virtual environment. Initialize git configuration.
- **Dependencies**: None.
- **Acceptance Criteria**:
  - `pip install -r requirements.txt` succeeds without errors.
  - Project imports load correctly under Python 3.10+.

### BL-102: SQLite Database Schema & Migration Script
- **Description**: Implement database connection class and migrations to create tables: `services`, `models`, `performance_metrics`, `system_config`.
- **Dependencies**: BL-101.
- **Acceptance Criteria**:
  - Migration script initializes tables.
  - Table schemas match those declared in `Architecture.md` exactly.

### BL-103: Windows Subprocess Manager
- **Description**: Implement `ProcessManager` to spawn, check, and terminate child processes under Windows. Must redirect I/O and capture PIDs.
- **Dependencies**: BL-101.
- **Acceptance Criteria**:
  - Starts standard executables (e.g. `ping.exe`) and captures PID.
  - Terminates process clean-up without leaving orphaned processes.

### BL-104: Windows Service Integration
- **Description**: Implement a service wrapper utilizing `pywin32` or an NSSM installer script to register the application as an automatic Windows Service.
- **Dependencies**: BL-103.
- **Acceptance Criteria**:
  - Service registers under `AIRuntimeManager`.
  - Service starts, stops, and restarts using Windows `Services.msc` or PowerShell `Get-Service`.

---

## Phase 2: Runtime Plugins & Config Synthesis

### BL-201: Plugin Base Class & Loader
- **Description**: Define the `BasePlugin` abstract class. Implement dynamic plugin loading from the `src/backend/app/plugins/` directory.
- **Dependencies**: BL-102.
- **Acceptance Criteria**:
  - Discovers and initializes all classes extending `BasePlugin` automatically.

### BL-202: Ollama Orchestration Plugin
- **Description**: Implement the plugin managing Ollama. Automates Ollama executable startup/shutdown, queries the model catalog via localhost API, and syncs models to the database.
- **Dependencies**: BL-103, BL-201.
- **Acceptance Criteria**:
  - Discovers installed local Ollama models.
  - Controls Ollama process lifecycle dynamically.

### BL-203: LiteLLM Configuration Synthesizer & Plugin
- **Description**: Create the LiteLLM plugin. Automatically generates the `litellm-config.yaml` based on active models and aliases in SQLite. Spawns LiteLLM process.
- **Dependencies**: BL-103, BL-201, BL-202.
- **Acceptance Criteria**:
  - Synthesizes valid LiteLLM configuration YAML.
  - LiteLLM server launches successfully.

### BL-204: OpenClaw Orchestration Plugin
- **Description**: Programmatic generation of `openclaw-config.yaml` and lifecycle management of the OpenClaw agent subprocess.
- **Dependencies**: BL-103, BL-201, BL-203.
- **Acceptance Criteria**:
  - Synthesizes valid OpenClaw config pointing to LiteLLM.

### BL-205: Model Context Protocol (MCP) Manager
- **Description**: Implement connection logic to run and interact with MCP Servers via stdio or SSE.
- **Dependencies**: BL-103, BL-201.
- **Acceptance Criteria**:
  - Boots registered MCP servers and lists their available tools.

---

## Phase 3: REST API & Monitoring

### BL-301: FastAPI Web Gateway
- **Description**: Implement the REST API using FastAPI. Exposes services control, model inventory, and system metrics endpoints.
- **Dependencies**: BL-102, BL-203.
- **Acceptance Criteria**:
  - Returns Swagger docs on `/docs`.
  - Service start/stop/restart endpoints execute actions correctly.

### BL-302: Health Monitor daemon
- **Description**: Build a background scheduler verifying port/socket and HTTP response states for active runtimes.
- **Dependencies**: BL-301.
- **Acceptance Criteria**:
  - Polls health every 10s.
  - Updates service status in SQLite on state transition.

### BL-303: Hardware Metrics Poller
- **Description**: Implement native Windows metrics querying for VRAM, GPU utilization, CPU, and RAM.
- **Dependencies**: BL-101.
- **Acceptance Criteria**:
  - Successfully queries GPU stats (utilization and VRAM) on NVIDIA/Windows systems.

---

## Phase 4: Single Page Dashboard

### BL-401: Frontend React Architecture Setup
- **Description**: Initialize the Vite + React client app. Configure build parameters to output files directly to FastAPI static directories.
- **Dependencies**: BL-301.
- **Acceptance Criteria**:
  - Client compiles and builds.
  - FastAPI serves the frontend on root URL (`/`).

### BL-402: Service Status & Metric Cards
- **Description**: Design widgets displaying running status, CPU, memory, VRAM, and average latency.
- **Dependencies**: BL-401, BL-303.
- **Acceptance Criteria**:
  - Displays actual values fetched from `/api/metrics` and `/api/services`.

### BL-403: Actions Panel & Log Viewer
- **Description**: Build button triggers (Start, Stop, Restart) and real-time logs terminal container.
- **Dependencies**: BL-402.
- **Acceptance Criteria**:
  - Clicking "Restart" fires POST requests and refreshes state.
  - Shows scrolling orchestrator log lines.

---

## Phase 5: Operations & Validation

### BL-501: Backup and Restore Utilities
- **Description**: Implement backup and restore tools wrapping SQLite DB and config directory into standard zip archives.
- **Dependencies**: BL-102, BL-203.
- **Acceptance Criteria**:
  - Saves file payload.
  - Restoring zip recovers previous database state and starts services correctly.

### BL-502: Benchmark Test Suite
- **Description**: Performance testing scripts calculating token throughput (token/s), latency, and queue queue depth.
- **Dependencies**: BL-301.
- **Acceptance Criteria**:
  - Generates markdown benchmark reports.

### BL-503: Final End-to-End Smoke Tests
- **Description**: Integration checks validating the entire pipeline: Service boot -> Model download -> LiteLLM configuration -> Inference routing.
- **Dependencies**: All.
- **Acceptance Criteria**:
  - Single command runs and passes all validation scenarios.
