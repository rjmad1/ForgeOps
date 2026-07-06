# ForgeOps User Guide

This guide is designed for daily users who interact with the ForgeOps platform (AI Runtime Manager). It details how to monitor, configure, and manage your local AI runtimes using the React Web Dashboard and the `arm` Command Line Interface (CLI).

---

## 1. Web Dashboard Operations

The Web Dashboard runs at `http://127.0.0.1:8088/`. It is structured into ten main pages, accessible via the left-side navigation menu:

```
+-------------------------------------------------------------+
| Home          | Key system statistics, active counts, resource gauges |
| Services      | Process toggle switches, port maps, status indicator   |
| Models        | Capabilities lists, provider details, metadata viewer|
| Health/Inv    | Hardware capabilities, tool environment logs         |
| Observability | Live hardware usage graphs (CPU, RAM, GPU, VRAM)      |
| Workflows     | Sequential setup steppers, start status indicators   |
| Event Stream  | Event audits, command dispatch history log          |
| Logs          | Live terminal output from child runtimes            |
| Settings      | Policy thresholds, retry limit, delays tuning       |
| Maintenance   | Updates dashboard, backup/restore buttons, bundle   |
+-------------------------------------------------------------+
```

### Key Daily Tasks on the Dashboard:
* **Toggle Theme**: Click the Sun/Moon icon in the upper-right corner to toggle between Dark Mode (default) and Light Mode.
* **Command Palette**: Press **Ctrl+K** to open the command search box. Type the name of any tab (e.g., "Logs") or action (e.g., "Toggle Theme") and press **Enter** to execute.
* **Monitor Transitions**: Real-time toast notifications will slide in at the bottom-right of the screen whenever a service changes status (e.g., `STARTING` -> `RUNNING`).

---

## 2. CLI Daily Workflows

The command-line interface tool, `arm`, is available globally in your system path.

### A. Service Status Assessment
To see all managed runtimes and system metrics at a glance:
```powershell
arm status
```
To query *only* the service statuses:
```powershell
arm services
```

### B. Controlling Services
Use start, stop, and restart commands followed by the service ID (`ollama`, `litellm`, `openclaw`, or `mcp`):
```powershell
arm start ollama
arm stop openclaw
arm restart litellm
```

### C. Model Capabilities Discovery
To check what local models have been installed or pulled:
```powershell
arm discover
```
This commands the plugins to query their respective local runtimes (e.g., querying Ollama's local tags API) and sync them into the SQLite database for LiteLLM gateway access.

### D. Viewing History Logs
Review command execution records and health failure history:
```powershell
arm history --limit 30
```

---

## 3. Logs & Diagnostics

### Viewing Logs
ForgeOps consolidates logs from all runtimes.
* **Via CLI**:
  ```powershell
  # To view the general orchestrator logs
  arm history
  
  # Or fetch log lines via REST API or files:
  # General logs reside at: C:\ProgramData\AIRuntimeManager\logs\service.log
  # Service logs reside at: C:\ProgramData\AIRuntimeManager\logs\<service_id>.log
  ```
* **Via Dashboard**: Navigate to the **Logs** tab. Select the target service from the dropdown list to view the tail end of its terminal output.

### System Diagnostics
To run a quick self-diagnostic report of the control plane configuration, service PIDs, and database entries:
```powershell
arm diagnostics
```

---

## 4. Maintenance Operations

Daily maintenance actions are grouped in the **Maintenance** tab of the dashboard, or triggered via the CLI.

### A. Support Bundles
If a service fails or behaves unexpectedly, generate a support bundle to send to administrator teams. The support bundle compresses all log files, database configurations, and active hardware specs into a single zip file.
* **CLI Command**:
  ```powershell
  arm support-bundle --output "C:\users\public\support_bundle.zip"
  ```
* **Dashboard Action**: Navigate to **Maintenance** and click **Download Support Bundle**.

### B. Backup & Restore
* **Create Backup**:
  ```powershell
  arm backup
  ```
  Creates a timestamped zip archive containing `arm.db` and active configuration parameters under `%PROGRAMDATA%\AIRuntimeManager\backups\`.
* **Restore Backup**:
  ```powershell
  arm restore --file "C:\ProgramData\AIRuntimeManager\backups\backup_20260706_100000\arm.db"
  ```

### C. Version Update Checks
Verify if newer versions of Ollama, LiteLLM, or OpenClaw are available:
* **Via Dashboard**: The **Maintenance** tab displays "Installed Version" versus "Latest Version".
* Clicking **Update** triggers the automated package download, executes service shutdown, installs the update, and restarts the service while verifying uptime.

---

## 5. Policies & Settings

The behavior of the orchestrator is controlled by dynamic policies. You can configure these in the **Settings & Policies** tab:

1. **Auto-Restart Policy**: Toggle `auto_restart_enabled` (`true`/`false`). If a runtime crashes unexpectedly, the orchestrator automatically schedules a restart.
2. **Restart Retries**: Adjust `auto_restart_limit` (number of times the orchestrator will try to restart a failing service before tripping the circuit breaker).
3. **Active Requests Block**: The `PreventLiteLLMStopWithActiveRequestsPolicy` prevents stopping the LiteLLM gateway if `litellm_active_requests` is greater than `0`. This protects running user sessions.

---

## 6. Daily Best Practices
* **Keep Daemon Running**: Ensure the `AIRuntimeManager` service is started before launching your IDE or developer agents.
* **Run Discovery after Pulling Models**: Whenever you run `ollama pull <model>`, make sure to run `arm discover` to sync the new model with the LiteLLM model catalog.
* **Check Free Disk Space**: Local LLMs are large (commonly 4GB–40GB). Periodically monitor your model inventory and prune unused models to prevent disk space exhaustion.
