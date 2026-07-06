# ForgeOps Version 1.1 Planning Backlog

This document outlines the product vision, roadmap milestones, Epic groups, and backlog specifications for the upcoming **ForgeOps Version 1.1** release.

---

## 1. Product Vision & Roadmap

### Product Vision (v1.1)
ForgeOps Version 1.1 focuses on improving developer experience on the workstation. We aim to achieve OS-agnostic execution (supporting macOS and Linux), integrate real-time SSE log streaming, and implement dynamic plugin loading.

### Roadmap Milestones
```
   Month 1: Cross-Platform Core      Month 2: Streaming & Metrics      Month 3: UI & IDE Integration
  ┌────────────────────────────┐    ┌───────────────────────────┐    ┌─────────────────────────────┐
  │ - Pathlib refactoring      │    │ - WebSockets / SSE logs   │    │ - VS Code Extension         │
  │ - Linux systemd integration│───►│ - SQLite WAL mode        │───►│ - CLI model downloader      │
  │ - Dynamic Plugin scan      │    │ - Real-time metrics charts│    │ - Security Log Sanitizer    │
  └────────────────────────────┘    └───────────────────────────┘    └─────────────────────────────┘
```

---

## 2. Epic Classifications

* **Epic 1: Platform Agnosticism (OS-agnostic)**: Decouple Windows-specific system paths and wrapper scripts to support macOS and Linux local runtimes.
* **Epic 2: Live Observability & Performance**: Transition from HTTP-polling of metrics and logs to WebSockets or SSE logs.
* **Epic 3: Developer Workflow Enhancements**: Expose CLI model pulling capabilities and build IDE configuration plugins.

---

## 3. Backlog Registers

### A. Feature Backlog

#### Item [F-1]: Direct Model Puller via CLI and UI
* **Problem Statement**: Users must open a separate command shell and run `ollama pull <model>` to download new models.
* **User Value**: Streamlines model management by allowing developers to download models directly from the ForgeOps dashboard or CLI.
* **Estimated Effort**: 3 Story Points (Medium)
* **Priority**: High
* **Dependencies**: None.

#### Item [F-2]: Custom Model Aliases & Routing
* **Problem Statement**: Users cannot register aliases to redirect a model request to a specific local model variant without manually editing YAML configs.
* **User Value**: Allows developers to map `gpt-4o` requests to local `llama3` variants inside the LiteLLM routing matrix via the dashboard.
* **Estimated Effort**: 5 Story Points (High)
* **Priority**: Medium
* **Dependencies**: [F-1]

---

### B. Technical Backlog

#### Item [T-1]: Dynamic Plugin Loading Registry
* **Problem Statement**: New plugins must be manually imported and registered in `main.py`, requiring code changes to extend the platform.
* **User Value**: Simplifies extension development. Placing a plugin file in `/plugins/` automatically registers it.
* **Estimated Effort**: 3 Story Points (Medium)
* **Priority**: High
* **Dependencies**: None.

#### Item [T-2]: Pathlib & OS-agnostic Path Refactoring
* **Problem Statement**: Windows paths (`%PROGRAMDATA%`) and command wrappers prevent compiling the application on Linux/macOS.
* **User Value**: Unlocks macOS and Linux support for developer workstations.
* **Estimated Effort**: 5 Story Points (High)
* **Priority**: Critical
* **Dependencies**: None.

---

### C. Operational Backlog

#### Item [O-1]: SQLite Write-Ahead Logging (WAL) Mode
* **Problem Statement**: Concurrent writes from the CLI, Dashboard, and background scheduler trigger database lock errors.
* **User Value**: Enables concurrent reads and writes, resolving database locks.
* **Estimated Effort**: 2 Story Points (Low)
* **Priority**: High
* **Dependencies**: None.

#### Item [O-2]: Automated Log File Rotation
* **Problem Statement**: Child process logs grow indefinitely, risking disk exhaustion.
* **User Value**: Prevents disk space exhaustion without user intervention.
* **Estimated Effort**: 2 Story Points (Low)
* **Priority**: Medium
* **Dependencies**: None.

---

### D. UX Backlog

#### Item [U-1]: Live Log Terminal View (FastAPI SSE / WebSockets)
* **Problem Statement**: The Dashboard Logs page polls the REST API every few seconds, causing high HTTP traffic and latency.
* **User Value**: Displays real-time terminal output logs with minimal latency and network overhead.
* **Estimated Effort**: 4 Story Points (Medium)
* **Priority**: High
* **Dependencies**: None.

---

### E. Security Backlog

#### Item [S-1]: Support Bundle Log Sanitization
* **Problem Statement**: Support bundle zips contain plaintext logs and configs which may leak developer secrets.
* **User Value**: Protects developer secrets when exporting logs to support.
* **Estimated Effort**: 3 Story Points (Medium)
* **Priority**: High
* **Dependencies**: [O-2]
