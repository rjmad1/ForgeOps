# Component Design: AI Runtime Manager

This document maps out the system components of the AI Runtime Manager and details their responsibilities.

```
┌────────────────────────────────────────────────────────┐
│                   Dashboard (React UI)                 │
└───────────────────────────┬────────────────────────────┘
                            │ REST API
┌───────────────────────────▼────────────────────────────┐
│                    FastAPI Web Server                  │
│  ┌──────────────────────┐      ┌────────────────────┐  │
│  │   Service Registry   │      │   Health Monitor   │  │
│  └──────────┬───────────┘      └─────────┬──────────┘  │
│             │                            │             │
│  ┌──────────▼───────────┐      ┌─────────▼──────────┐  │
│  │  Config Manager      │      │   Model Manager    │  │
│  └──────────┬───────────┘      └─────────┬──────────┘  │
│             │                            │             │
│  ┌──────────▼───────────┐      ┌─────────▼──────────┐  │
│  │   Runtime Manager    │      │  Process Manager   │  │
│  └──────────────────────┘      └────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

## Detailed Modules

### 1. Service Registry (`service_registry.py`)
- **Responsibility**: Database interface for registering, querying, and updating service records in SQLite.
- **Key Methods**:
  - `register_service(service: ServiceSchema)`
  - `get_service(service_id: str) -> Service`
  - `update_service_status(service_id: str, status: str)`
  - `list_services() -> List[Service]`

### 2. Process Manager (`process_manager.py`)
- **Responsibility**: Low-level execution of OS processes. Manages PIDs, handles subprocess I/O pipes, and performs safe, clean termination on Windows using `psutil`.
- **Key Methods**:
  - `start_process(binary_path: str, args: List[str], env: dict) -> int` (Returns PID)
  - `stop_process(pid: int) -> bool`
  - `is_process_running(pid: int) -> bool`
  - `get_process_metrics(pid: int) -> Dict[str, Any]` (CPU, RAM)

### 3. Configuration Manager (`config_manager.py`)
- **Responsibility**: Programmatic configuration generation. Consumes global settings and writes structured YAML/JSON to target files for Ollama, LiteLLM, and OpenClaw.
- **Key Methods**:
  - `generate_litellm_config() -> str`
  - `generate_openclaw_config() -> str`
  - `sync_all_configs()`

### 4. Health Monitor (`health_monitor.py`)
- **Responsibility**: Runs background timers to verify the HTTP/TCP responsiveness of services. Integrates with the Service Registry to update statuses.
- **Key Methods**:
  - `check_http_endpoint(port: int, path: str) -> bool`
  - `check_tcp_port(port: int) -> bool`
  - `run_monitoring_loop()`

### 5. Model Manager (`model_manager.py`)
- **Responsibility**: Dynamically inspects local providers to discover models, then syncs them with the SQLite `models` table.
- **Key Methods**:
  - `discover_all_models()`
  - `categorize_model(model_name: str, meta: dict) -> str`
  - `get_active_models() -> List[Model]`

### 6. Diagnostics & Update Manager (`diagnostics.py`, `update_manager.py`)
- **Responsibility**: Aggregates structured logs, checks platform status, executes latency benchmarks, and downloads updates for local components.
- **Key Methods**:
  - `run_system_diagnostics() -> Dict[str, Any]`
  - `trigger_backup() -> str` (Returns archive path)
  - `trigger_restore(archive_path: str) -> bool`
  - `check_component_updates() -> List[Dict[str, Any]]`
