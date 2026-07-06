# ForgeOps Repository Health Report

This report summarizes key code and structure metrics collected from the **ForgeOps Version 1.0** repository.

---

## 1. Repository Footprint & Metrics

* **Clean Files Count**: 176 files (excluding `node_modules`, `.venv`, `.git`, `.pytest_cache`, and frontend `dist/` folders).
* **Total Size**: 1.24 MB (1,271 KB).
* **Source Python Lines of Code (LOC)**: 4,429
* **Test Python Lines of Code (LOC)**: 1,417
* **Code-to-Test Ratio**: `3.1 : 1` (a test coverage footprint of `32%` relative to source code).

---

## 2. Dependency Inventory

### A. Python Backend Dependencies (`requirements.txt`)
* `fastapi==0.139.0` (REST framework)
* `uvicorn[standard]==0.50.0` (ASGI server engine)
* `pywin32==312` (Native Windows API wrapper)
* `psutil==7.2.2` (Process monitoring & metrics)
* `pyyaml==6.0.3` (YAML file compiler)
* `pydantic==2.13.4` (Data models validations)
* `pytest==9.1.1` & `pytest-cov==7.1.0` (Test execution)
* `httpx==0.28.1` (HTTP API client)

### B. JavaScript Frontend Dependencies (`package.json`)
* `lucide-react@1.23.0` (Icon assets library)
* `react@19.2.7` & `react-dom@19.2.7` (UI framework core)
* **Dev Tools**: `vite@8.1.3`, `typescript@6.0.3`, `oxlint@1.72.0` (Linter).

---

## 3. License Inventory
* **Core Project License**: MIT (declared in root `LICENSE` file).
* **Third-Party Libraries**: Checked via `scripts/LICENSE-3RD-PARTY.txt`:
  * Python dependencies (fastapi, uvicorn, pydantic, pyyaml, httpx): BSD / MIT / Apache 2.0.
  * Node modules (React, Vite, Lucide): MIT / BSD.
  * System tools (Ollama, Git): MIT / GPL.

---

## 4. Architectural inventories

### A. Active Plugins Inventory
Four plugins are registered in the `ControlPlaneKernel`:
1. `ollama` (Ollama Daemon Plugin)
2. `litellm` (LiteLLM Gateway Plugin)
3. `openclaw` (OpenClaw Supervisor Plugin)
4. `mcp` (Model Context Protocol Hub Plugin)

### B. REST API Endpoints Inventory
The FastAPI backend exposes 32 active routes (including v1 and aliases). Key paths:
* `/health` (Health liveness)
* `/api/v1/services` & `/api/services` (Service listing)
* `/api/v1/services/{id}/start` & `/api/services/{id}/start` (Lifecycle triggers)
* `/api/v1/services/{id}/logs` & `/api/logs` (Subprocess logs)
* `/api/v1/models` & `/api/models` (Capability catalog)
* `/api/models/discover` & `/api/v1/inventory/discover` (Discovery scans)
* `/api/v1/system/metrics` & `/api/metrics` (System loads)
* `/api/v1/diagnostics/report` & `/api/v1/diagnostics/support-bundle` (Diagnostics)
* `/api/v1/operations/backup` & `/api/v1/operations/restore` (Backup/Restore)
* `/api/v1/operations/benchmark` (Performance measurements)
* `/api/v1/auth/token` (Authentication tokens)

### C. CLI Commands Inventory
The `arm` console script exposes 13 subcommands:
* `services`, `status`, `start`, `stop`, `restart`, `inventory`, `discover`, `history`, `diagnostics`, `support-bundle`, `backup`, `restore`, `benchmark`.

---

## 5. Complexity Summary

* **Cyclomatic Complexity**: Low-to-Medium.
* **Analysis**:
  * **Domain Layer**: Highly modular. Domain methods (commands, events, policies) are thin with complexity values $\le 4$.
  * **Persistence Layer**: Structured Repository interfaces. Complex mappings are delegated to Sqlite SQLite schemas.
  * **API Layer (`main.py`)**: Individual endpoint route handlers are decoupled, with complexity ranges of $4 - 8$ (mostly handling HTTP exceptions).
  * **Installer Layer (`install.py`)**: Has the highest complexity ($\approx 12$) due to nested prerequisite checks and platform validation logic.
