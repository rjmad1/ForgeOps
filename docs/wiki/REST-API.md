# ForgeOps REST API Reference

The ForgeOps (AI Runtime Manager) REST API is built on FastAPI. It runs on loopback `127.0.0.1:8088`. All requests and responses are formatted as JSON payloads.

---

## Authentication & Headers

Requests targeting `/api/` (except `/api/v1/auth/token`) require authentication via one of two methods:
1. **API Key Header**: Include `X-API-Key` containing the active session API token.
2. **Session Cookie**: Include the `session_api_key` cookie set during initial root handshake.

*To obtain the session key programmatically:*
Perform a `GET` request to `http://127.0.0.1:8088/api/v1/auth/token` from a local client (which is allowed bypass permissions).

---

## 1. System Health & Auth Endpoints

### GET `/health`
* **Purpose**: Simple liveness check.
* **Authentication**: None.
* **Response Example (200 OK)**:
  ```json
  {"status": "healthy"}
  ```

### GET `/api/v1/auth/token`
* **Purpose**: Retrieve the active session token.
* **Authentication**: None (restricted to loopback interface).
* **Response Example (200 OK)**:
  ```json
  {"token": "d748f2bc5a6e8790f12ab345cd67ef890123456789abcdef0123456789abcde"}
  ```

### GET `/api/v1/health`
* **Purpose**: Detailed health status of all managed runtimes.
* **Authentication**: Required.
* **Response Example (200 OK)**:
  ```json
  {
    "status": "healthy",
    "services": {
      "ollama": "RUNNING",
      "litellm": "RUNNING",
      "openclaw": "STOPPED",
      "mcp": "RUNNING"
    }
  }
  ```

---

## 2. Service Management Endpoints

### GET `/api/v1/services`
* **Aliases**: `GET /api/services`
* **Purpose**: List all registered AI runtimes.
* **Query Parameters**:
  * `refresh` (Boolean, optional): Set `true` to force a health probe scan.
* **Response Example (200 OK)**:
  ```json
  [
    {
      "id": "ollama",
      "name": "Ollama Daemon",
      "type": "ollama",
      "port": 11434,
      "status": "RUNNING",
      "pid": 7420,
      "binary_path": "C:\\ProgramData\\Ollama\\ollama.exe",
      "args": "serve",
      "config_path": null,
      "auto_start": true
    }
  ]
  ```

### GET `/api/v1/services/{service_id}`
* **Aliases**: `GET /api/services/{service_id}`
* **Purpose**: Retrieve details of a single service.
* **Response Example (200 OK)**:
  ```json
  {
    "id": "litellm",
    "name": "LiteLLM Gateway",
    "type": "litellm",
    "port": 8000,
    "status": "RUNNING",
    "pid": 8116,
    "binary_path": "litellm",
    "args": ["--port", "8000"],
    "config_path": "litellm_config.yaml",
    "auto_start": true
  }
  ```

### POST `/api/v1/services/{service_id}/start`
* **Aliases**: `POST /api/services/{service_id}/start`
* **Purpose**: Start a stopped service process.
* **Response Example (200 OK)**:
  ```json
  {"status": "RUNNING", "pid": 9324}
  ```

### POST `/api/v1/services/{service_id}/stop`
* **Aliases**: `POST /api/services/{service_id}/stop`
* **Purpose**: Stop a running service process.
* **Response Example (200 OK)**:
  ```json
  {"status": "STOPPED"}
  ```

### POST `/api/v1/services/{service_id}/restart`
* **Aliases**: `POST /api/services/{service_id}/restart`
* **Purpose**: Restart a service.
* **Response Example (200 OK)**:
  ```json
  {"status": "RUNNING", "pid": 9412}
  ```

---

## 3. Logs & Diagnostics

### GET `/api/v1/services/{service_id}/logs`
* **Aliases**: `GET /api/logs?service_id={service_id}`
* **Purpose**: Tail the console output files for a service.
* **Query Parameters**:
  * `limit` (Integer, default=100): Number of tail lines to retrieve.
* **Response Example (200 OK)**:
  ```json
  {
    "service_id": "ollama",
    "logs": [
      "2026-07-06T10:00:00Z INFO starting ollama serve",
      "2026-07-06T10:00:02Z INFO listening on 127.0.0.1:11434"
    ],
    "log_file_path": "C:\\ProgramData\\AIRuntimeManager\\logs\\ollama.log"
  }
  ```

### GET `/api/v1/diagnostics/report`
* **Purpose**: Generate system-wide self-diagnostics JSON.
* **Response Example (200 OK)**:
  ```json
  {
    "timestamp": "2026-07-06T10:45:00.123456",
    "services": [...],
    "models": [...],
    "inventory": [...],
    "configs": {
      "auto_restart_enabled": "true",
      "auto_restart_limit": "2"
    },
    "history": [...]
  }
  ```

### GET `/api/v1/diagnostics/support-bundle`
* **Purpose**: Generate and download support bundle zip.
* **Response**: Binary stream (`application/zip` download).

---

## 4. Models & Capabilities

### GET `/api/v1/models`
* **Aliases**: `GET /api/models`
* **Purpose**: List discovered local LLM capabilities.
* **Response Example (200 OK)**:
  ```json
  [
    {
      "id": "ollama/llama3",
      "name": "llama3",
      "type": "model",
      "provider": "ollama",
      "metadata": {
        "size_bytes": 4661234567,
        "family": "llama",
        "parameter_size": "8B",
        "quantization_level": "Q4_0"
      }
    }
  ]
  ```

### POST `/api/models/discover`
* **Purpose**: Force discovery scan.
* **Response Example (200 OK)**:
  ```json
  {
    "status": "completed",
    "models_discovered": 3
  }
  ```

---

## 5. Operations & Maintenance

### POST `/api/v1/operations/backup`
* **Aliases**: `POST /api/operations/backup`
* **Purpose**: Archive SQLite database and configuration files.
* **Response Example (200 OK)**:
  ```json
  {
    "status": "success",
    "backup_file": "C:\\ProgramData\\AIRuntimeManager\\backups\\backup_20260706_105000.zip"
  }
  ```

### POST `/api/v1/operations/restore`
* **Aliases**: `POST /api/operations/restore`
* **Purpose**: Restore state database from file path.
* **Request Body Example**:
  ```json
  {"backup_file": "C:\\ProgramData\\AIRuntimeManager\\backups\\backup_20260706_105000.zip"}
  ```
* **Response Example (200 OK)**:
  ```json
  {"status": "success"}
  ```

### POST `/api/v1/operations/benchmark`
* **Aliases**: `POST /api/operations/benchmark`
* **Purpose**: Measure latency and throughput of the active model.
* **Response Example (200 OK)**:
  ```json
  {
    "model": "llama3",
    "provider": "ollama",
    "ttft_ms": 320.5,
    "tokens_per_second": 18.4,
    "report_path": "C:\\ProgramData\\AIRuntimeManager\\benchmarks\\benchmark_report.md"
  }
  ```

---

## 6. Metrics & Performance

### GET `/api/v1/system/metrics`
* **Aliases**: `GET /api/metrics`
* **Purpose**: Query current system resources (CPU, RAM, GPU, VRAM).
* **Response Example (200 OK)**:
  ```json
  {
    "cpu": {
      "utilization_pct": 14.2
    },
    "ram": {
      "total_bytes": 17179869184,
      "available_bytes": 9437184000,
      "used_bytes": 7742685184,
      "utilization_pct": 45.1
    },
    "gpu": {
      "available": true,
      "name": "NVIDIA GeForce RTX 4070",
      "utilization_pct": 10.5,
      "vram_used_bytes": 1887436800,
      "vram_total_bytes": 12884901888
    }
  }
  ```

---

## Error Payloads

When errors are encountered, the API returns standard HTTP error codes accompanied by a descriptive JSON payload:

```json
{
  "detail": "Error explanation text"
}
```

* **401 Unauthorized**: Session token invalid or missing.
* **404 Not Found**: Service ID or key configuration does not exist.
* **500 Internal Server Error**: Process execution failed or hardware exception raised.
