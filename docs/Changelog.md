# Changelog: ForgeOps

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-07-06

### Added
- **Windows Service Host**: Created `setup_service.py` to register the web server as a native Windows service.
- **Process Manager**: Implemented `process_manager.py` with robust process group control, process metrics parsing, and clean termination.
- **Plugins**: Built `OllamaPlugin`, `LiteLLMPlugin`, `OpenClawPlugin`, and `McpPlugin` for automated configurations.
- **FastAPI Web API**: Designed REST API endpoints with Swagger schema docs and Local API key authentication middleware.
- **Health Engine**: Formulated liveness probes and backoff/restart handlers with circuit breaker support.
- **Hardware Telemetry**: Programmed a metrics poller for CPU, RAM, and GPU tracking (via `nvidia-smi` parser).
- **React UI Dashboard**: Engineered a responsive Vite + React single-page frontend.
- **System Validation**: Authored `validate_system.py` covering install, rollback, CLI, REST API, and auto-restart validation checks.
- **GitHub community files**: Created `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `GOVERNANCE.md`.

### Fixed
- **SQLite Database locking**: Closed SQLite cursor handles explicitly in validation checks to prevent locked file exceptions on Windows.
- **Uvicorn API server startup delay**: Raised wait timeout from 5s to 15s to allow for full startup checks.
- **Health Engine restart timeout**: Swapped client timeouts to 15s for the auto-restart checks to avoid ReadTimeout exceptions on slower environments.
