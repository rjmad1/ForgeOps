# Software Requirements Specification (SRS): AI Runtime Manager

This document defines the functional and non-functional requirements for the AI Runtime Manager platform.

## Functional Requirements

### 1. Windows Service Orchestration (FR-1)
- **FR-1.1**: The application must run as a native Windows Service that starts automatically on system boot.
- **FR-1.2**: The service must execute subprocesses (Ollama, LiteLLM, OpenClaw, MCP) and manage their lifecycles.
- **FR-1.3**: The service must handle clean process termination (graceful SIGINT, fallback to `taskkill` if unresponsive).

### 2. Service & Process Management (FR-2)
- **FR-2.1**: The system must provide Start, Stop, and Restart APIs and CLI commands for every registered service.
- **FR-2.2**: The system must monitor PIDs and CPU/RAM usage of child processes.
- **FR-2.3**: If a service crashes, the Process Manager must restart it up to 3 times before transitioning it to the `ERROR` state.

### 3. Dynamic Model Discovery (FR-3)
- **FR-3.1**: The system must automatically query the Ollama engine (`/api/tags`) to discover installed models.
- **FR-3.2**: The system must parse LiteLLM model configs to extract active aliases.
- **FR-3.3**: The system must categorize models into `embedding`, `vision`, `reasoning`, `coding`, and `general` based on model metadata and names.
- **FR-3.4**: Model names must never be hardcoded.

### 4. Configuration Synthesis (FR-4)
- **FR-4.1**: Users must not edit YAML/JSON configs directly.
- **FR-4.2**: The system must generate `config.yaml` for LiteLLM containing local model definitions, ports, and aliases.
- **FR-4.3**: The system must synthesize configuration files for OpenClaw and MCP servers dynamically.

### 5. Unified Gateway & Health Monitoring (FR-5)
- **FR-5.1**: Provide a single unified OpenAI-compatible routing port.
- **FR-5.2**: The Health Monitor must poll endpoints every 10 seconds.
- **FR-5.3**: Track metrics: Active connections, Average Response Time (ART), and queue depth.

### 6. Single Page Dashboard (FR-6)
- **FR-6.1**: Single page visual dashboard in React showing all running/installed services.
- **FR-6.2**: Show real-time hardware status: GPU utilization, VRAM usage, RAM usage, and CPU load.
- **FR-6.3**: Implement button actions: Start, Stop, Restart, Update, Backup, Restore, Benchmark, and Diagnostics.
- **FR-6.4**: Embed live-tailing log console.

---

## Non-Functional Requirements

### 1. Operating System & Platform (NFR-1)
- **NFR-1.1**: The platform must target Windows 11 Professional.
- **NFR-1.2**: Shell operations must use native PowerShell or cmd.
- **NFR-1.3**: Database storage must use SQLite 3.

### 2. Extensibility (NFR-2)
- **NFR-2.1**: Runtimes must be built as plugins. Adding a new runtime plugin must require zero changes to the core orchestrator.

### 3. Reliability & Recovery (NFR-3)
- **NFR-3.1**: System recovery must happen automatically on crash (restart within 5 seconds).
- **NFR-3.2**: The system must maintain an audit log of all service state changes in SQLite.

### 4. Performance (NFR-4)
- **NFR-4.1**: Memory footprint of the core service must remain under 150MB RAM when idle.
- **NFR-4.2**: Metrics aggregation polling must consume less than 1% of CPU cycles.
