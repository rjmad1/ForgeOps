# ForgeOps Technical Debt Register

This register tracks structural limitations, architectural shortcuts, and testing gaps in **ForgeOps Version 1.0** that should be resolved in future release cycles (such as Version 1.1 or Version 2).

---

## 1. Active Technical Debt Ledger

### A. Database Concurrency Limitations
* **Description**: The database persistence layer uses a local SQLite instance (`arm.db`). SQLite locks the database file during write transactions.
* **Impact**: Low on single-user developer workstations. If multiple client tools (e.g. CLI, UI, and external IDE extensions) attempt to write simultaneously, one of them will fail with a `database is locked` error.
* **Mitigation**: Future releases should implement a retry/busy-handler wrapper or migrate to a server-client storage engine if multi-client usage increases.

### B. Tight Coupling to Windows OS
* **Description**: System directory paths (`%PROGRAMDATA%`), Windows backslashes, service control commands (`sc.exe`), and `pywin32` API bindings are hardcoded.
* **Impact**: High for cross-platform compatibility. The daemon will not run on macOS or Linux without significant overrides.
* **Mitigation**: Wrap system paths in python `pathlib` and abstract the service control calls behind an OS-agnostic process manager framework.

### C. Plaintext Logs in Support Bundles
* **Description**: The support bundle compiler packs raw stdout logs and database configuration files into a zip.
* **Impact**: Medium. If a developer has hardcoded tokens in their logs or configurations, they will be exported in plaintext in the support bundle zip.
* **Mitigation**: Add a sanitization step to strip API tokens or personal identifying info (PII) before packaging logs.

### D. Poll-Based Log Streaming
* **Description**: Log tailing in the dashboard logs tab periodically executes HTTP `GET` requests to tail lines instead of streaming.
* **Impact**: Medium. Results in high HTTP request counts and higher network load on loopback ports when logs are open in the browser.
* **Mitigation**: Integrate FastAPI Server-Sent Events (SSE) or WebSockets in the logs controller for real-time, low-overhead streaming.

### E. Static Plugin Registry
* **Description**: Runtimes must be registered statically in `main.py`.
* **Impact**: Low. Adding a custom plugin requires editing `main.py` and recompiling/restarting the orchestrator.
* **Mitigation**: Implement a dynamic loading mechanism that scans the `plugins/` directory and auto-loads subclasses of `RuntimePlugin` on startup.

### F. Integration Test Mock Dependency
* **Description**: Test suites mock the process manager subprocess runs and Ollama/LiteLLM REST endpoints.
* **Impact**: Medium. Changes in downstream tool APIs (e.g. a change in Ollama's local ports or config yaml syntax) will not be caught by local unit/integration tests until runtime checks.
* **Mitigation**: Implement a set of active-stage integration tests that run on test environments with live tool dependencies.
