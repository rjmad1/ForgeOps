# ForgeOps Administrator Guide

This guide is written for system administrators, enterprise architects, and support engineers responsible for configuring, securing, and maintaining the ForgeOps (AI Runtime Manager) service infrastructure on Windows workstations.

---

## 1. System Topology & Architecture

ForgeOps is implemented as a local background daemon running as a Windows Service, wrapping a FastAPI REST application and a SQLite persistence layer. It manages downstream AI runtime engines (Ollama, LiteLLM, OpenClaw, and Model Context Protocol) as subprocesses.

```
                  ┌───────────────────────────────┐
                  │      REST / UI Clients        │
                  └───────────────┬───────────────┘
                                  │ Loopback TCP (Port 8088)
                                  ▼
                  ┌───────────────────────────────┐
                  │    FastAPI Gateway Daemon     │
                  │   (AIRuntimeManager Service)  │
                  └──────┬────────────────┬───────┘
                         │                │
            Reads/Writes │                │ Spawns & Controls
                         ▼                ▼
                  ┌────────────┐    ┌─────────────────────────────┐
                  │ SQLite DB  │    │       Process Manager       │
                  │  (arm.db)  │    └─────────────┬───────────────┘
                  └────────────┘                  │
                                                  ├─► Ollama Daemon (Port 11434)
                                                  ├─► LiteLLM Proxy (Port 8000)
                                                  ├─► OpenClaw Agent (Port 8080)
                                                  └─► MCP Stdio/SSE Servers
```

---

## 2. Configuration & State Management

ForgeOps uses a hybrid configuration system:
1. **Local Properties**: Initial settings are configured via the database.
2. **SQLite Database Configuration (`system_config`)**: Active orchestrator parameters are stored in the database.

### System Configuration Keys (in `system_config` table):
Administrators can modify these parameters dynamically using the **Settings** tab in the dashboard or via SQL injections to `arm.db`:

| Configuration Key | Data Type | Default Value | Purpose |
|---|---|---|---|
| `auto_restart_enabled` | Boolean (`true`/`false`) | `true` | Toggle reactive auto-restart logic. |
| `auto_restart_limit` | Integer | `2` | Maximum retry attempts before tripping the circuit breaker. |
| `auto_restart_base_delay` | Float | `2.0` | Initial restart delay in seconds. |
| `auto_restart_max_delay` | Float | `30.0` | Cap on exponential backoff delays. |
| `auto_restart_multiplier` | Float | `2.0` | Backoff multiplier for successive failures. |
| `auto_restart_jitter_pct` | Float | `0.2` | Random variation percentage to prevent resource thundering. |
| `auto_restart_cooldown` | Float | `10.0` | Uptime threshold (in seconds) to reset the failure counter. |
| `auto_restart_window` | Float | `60.0` | Time window (in seconds) inside which retry count applies. |
| `litellm_active_requests` | Integer | `0` | Live request counter (used to block stopping commands). |

---

## 3. Windows Service Registration

The core FastAPI application runs persistently inside a native Windows Service named `AIRuntimeManager`.

### Service Control via PowerShell:
* **Start Service**: `Start-Service -Name AIRuntimeManager`
* **Stop Service**: `Stop-Service -Name AIRuntimeManager`
* **Service Status**: `Get-Service -Name AIRuntimeManager`
* **Startup Type Modification**: `Set-Service -Name AIRuntimeManager -StartupType Automatic`

### Technical Implementation:
The service wrapper is implemented in `src/backend/setup_service.py` using Python's native `win32serviceutil` package. 
* To register the service manually:
  ```powershell
  python src/backend/setup_service.py install
  ```
* To update the service binaries location:
  ```powershell
  python src/backend/setup_service.py update
  ```
* To remove the service:
  ```powershell
  python src/backend/setup_service.py remove
  ```

---

## 4. Security & Permissions hardening

To align with corporate compliance guidelines (IVV-SEC-01 & IVV-SEC-02), the following security boundaries are enforced:

### A. Network Interface Bindings
* The FastAPI gateway, LiteLLM, Ollama, and OpenClaw services must bind strictly to the loopback interface (`127.0.0.1` or `localhost`).
* External network connections are rejected. CORS is locked down to local Vite ports:
  ```python
  allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8088", "http://127.0.0.1:8088"]
  ```

### B. Session API Key Security
* On startup, the control plane generates a cryptographically secure 32-byte hexadecimal session token (`session_api_key`).
* This token is saved to `%PROGRAMDATA%\AIRuntimeManager\.session_api_key`.
* **Access Control Lists (ACLs)**: The setup script uses Windows Security APIs to restrict access to this file. It strips inherited permissions and explicitly grants **Full Control** *only* to:
  1. `SYSTEM` (S-1-5-18)
  2. `Administrators` (S-1-5-32-544)
  3. The current user SID (process owner).
* Standard/unprivileged workstation users cannot read this token.

---

## 5. Performance Tuning & Resource Controls

To ensure local model execution does not starve developer tools:
1. **Exponential Backoff**: Configure the backoff parameters (`auto_restart_multiplier` and `auto_restart_base_delay`) to prevent thundering herds on GPU memory during service boot failures.
2. **Circuit Breakers**: Ensure `auto_restart_limit` is set low (e.g., `2` or `3`). If a service fails to initialize due to a port conflict or driver crash, the breaker trips (status shifts to `OPEN`), halting CPU thrashing.
3. **Database Maintenance**: SQLite performs incremental writes. To clean storage allocations, run vacuum maintenance tasks monthly:
   ```powershell
   # Open SQLite shell or query via admin CLI
   sqlite3 C:\ProgramData\AIRuntimeManager\db\arm.db "VACUUM;"
   ```
4. **Log Rotation**: Subprocess logs are saved in `%PROGRAMDATA%\AIRuntimeManager\logs\`. It is recommended to configure a weekly task to compress or purge log files exceeding 100MB.
