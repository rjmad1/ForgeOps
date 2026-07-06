# ForgeOps CLI Reference

The ForgeOps command-line interface client, `arm`, acts as the control point for managing runtime daemons, inspecting metrics, executing backups, and triggering model discovery.

---

## Command Syntax Conventions

All commands follow the structure:
```powershell
arm <subcommand> [arguments] [options]
```

### Global Environment Variables:
* `ARM_API_URL`: Override the target API endpoint URL (defaults to `http://127.0.0.1:8088`).

---

## 1. Services Management Subcommands

### `arm services`
* **Purpose**: List all registered services, their current status, listening port, and PID.
* **Syntax**:
  ```powershell
  arm services
  ```
* **Expected Output**:
  ```text
  Service ID      | Service Name                   | Port   | Status       | PID
  ---------------------------------------------------------------------------
  ollama          | Ollama Daemon                  | 11434  | RUNNING      | 7420
  litellm         | LiteLLM Gateway                | 8000   | STOPPED      | -
  ```
* **Related Commands**: `arm status`.

---

### `arm status`
* **Purpose**: Show service registry statuses alongside detailed host system resource metrics.
* **Syntax**:
  ```powershell
  arm status
  ```
* **Expected Output**:
  ```text
  === Managed Services ===
  Service ID      | Service Name                   | Port   | Status       | PID
  ---------------------------------------------------------------------------
  ollama          | Ollama Daemon                  | 11434  | RUNNING      | 7420
  ...
  
  === System Resource Consumption ===
    CPU Utilization : 8.2%
    RAM Utilization : 38.5% (6300 MB / 16384 MB)
    GPU Availability: No NVIDIA GPU detected or nvidia-smi failed.
  ```
* **Related Commands**: `arm services`.

---

### `arm start <service_id>`
* **Purpose**: Launch a managed subprocess runtime.
* **Parameters**:
  * `<service_id>`: ID of the service (e.g. `ollama`, `litellm`, `openclaw`, `mcp`).
* **Syntax**:
  ```powershell
  arm start <service_id>
  ```
* **Example**:
  ```powershell
  arm start ollama
  ```
* **Expected Output**:
  ```text
  Dispatching start command for 'ollama'...
  Success. Service status: RUNNING, PID: 12480
  ```
* **Common Errors**:
  * `Error: Control plane daemon is offline`: Verify the `AIRuntimeManager` service is started.
  * `Error starting service: Port already in use`: Another tool occupies the service's port.

---

### `arm stop <service_id>`
* **Purpose**: Terminate a running subprocess runtime cleanly.
* **Parameters**:
  * `<service_id>`: ID of the service to stop.
* **Syntax**:
  ```powershell
  arm stop <service_id>
  ```
* **Example**:
  ```powershell
  arm stop litellm
  ```
* **Expected Output**:
  ```text
  Dispatching stop command for 'litellm'...
  Success. Service status: STOPPED
  ```

---

### `arm restart <service_id>`
* **Purpose**: Restarts a service process.
* **Parameters**:
  * `<service_id>`: ID of the target service.
* **Syntax**:
  ```powershell
  arm restart <service_id>
  ```
* **Example**:
  ```powershell
  arm restart ollama
  ```

---

## 2. Capabilities & Discovery

### `arm discover`
* **Purpose**: Force a system capability scan of all plugins to discover active local models.
* **Syntax**:
  ```powershell
  arm discover
  ```
* **Expected Output**:
  ```text
  Dispatching discovery scan command...
  Success. Status: completed. Local models discovered: 4
  ```
* **Related Commands**: `arm services` (run `arm services` with database check updates).

---

### `arm inventory`
* **Purpose**: Dump discovered system hardware components, paths, and environment tools.
* **Syntax**:
  ```powershell
  arm inventory
  ```
* **Expected Output**:
  ```text
  === Discovered Host System Inventory ===
  
  [OS] os_details:
    platform: win32
    version: 10.0.22631
    release: 11
  
  [GPU] nvidia_gpu:
    name: NVIDIA GeForce RTX 4070 Laptop GPU
    vram_total_mb: 8188
  ```

---

## 3. Maintenance & Monitoring

### `arm history`
* **Purpose**: View recent orchestrator event history and health alerts.
* **Parameters**:
  * `--limit <n>` (Integer, default=20): Number of logs to retrieve.
* **Syntax**:
  ```powershell
  arm history [--limit <n>]
  ```
* **Expected Output**:
  ```text
  Timestamp               | Type               | Severity | Message
  --------------------------------------------------------------------------------------------------
  2026-07-06T10:40:02.123 | SERVICE_RESTART    | WARNING  | Service litellm failed. Auto-restarting in 2.0s.
  2026-07-06T10:40:04.234 | SERVICE_START      | INFO     | Service litellm successfully started.
  ```

---

### `arm diagnostics`
* **Purpose**: Generate self-diagnostics checks summarizing service registrations and discovered models.
* **Syntax**:
  ```powershell
  arm diagnostics
  ```
* **Expected Output**:
  ```text
  === AI Control Plane Diagnostics ===
  Overall status: DEGRADED
  Active Plugins/Services count: 4
  Active Discovered Models count: 3
  
  Service Health Breakdown:
    - Ollama Daemon (ollama): RUNNING
    - LiteLLM Gateway (litellm): ERROR
    - OpenClaw Supervisor (openclaw): STOPPED
    - Model Context Protocol Hub (mcp): RUNNING
  ```

---

### `arm support-bundle`
* **Purpose**: Assemble database configurations and logs into a zip bundle.
* **Parameters**:
  * `--output <path>` (String, default="support_bundle.zip"): Path of destination archive.
* **Syntax**:
  ```powershell
  arm support-bundle [--output <path>]
  ```

---

### `arm backup`
* **Purpose**: Back up the SQLite database and yaml configuration parameters into a timestamped zip.
* **Syntax**:
  ```powershell
  arm backup
  ```
* **Expected Output**:
  ```text
  Initiating configuration and database backup...
  Success. Backup zip file created at: C:\ProgramData\AIRuntimeManager\backups\backup_20260706_105500.zip
  ```

---

### `arm restore`
* **Purpose**: Restore database configurations from an archive.
* **Parameters**:
  * `--file <path>` (String, required): Path to backup zip.
* **Syntax**:
  ```powershell
  arm restore --file <path>
  ```
* **Example**:
  ```powershell
  arm restore --file C:\ProgramData\AIRuntimeManager\backups\backup_20260706_105500.zip
  ```

---

### `arm benchmark`
* **Purpose**: Benchmark inference performance (Time-To-First-Token and speed) on the active model.
* **Syntax**:
  ```powershell
  arm benchmark
  ```
* **Expected Output**:
  ```text
  Running inference benchmark suite (evaluating active model)...
  Benchmark Execution Succeeded.
    Model   : llama3
    Provider: ollama
    TTFT    : 340.2 ms
    Speed   : 17.5 tokens/sec
    Report  : C:\ProgramData\AIRuntimeManager\benchmarks\benchmark_report.md
  ```
