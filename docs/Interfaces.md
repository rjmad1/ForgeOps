# Interfaces & Contracts: AI Runtime Manager

This document outlines the REST API endpoints, Command Line Interface (CLI) syntax, and plugin contracts.

## REST API Endpoints (FastAPI)

All endpoints return JSON responses. Errors use standard HTTP status codes with a JSON error payload: `{"detail": "Error message"}`.

### 1. Service Management
- **GET** `/api/services`  
  *Returns*: List of registered services and their current status.
- **GET** `/api/services/{id}`  
  *Returns*: Detailed status, PID, and configuration of a single service.
- **POST** `/api/services/{id}/start`  
  *Returns*: `{"status": "starting", "pid": 1234}`
- **POST** `/api/services/{id}/stop`  
  *Returns*: `{"status": "stopped"}`
- **POST** `/api/services/{id}/restart`  
  *Returns*: `{"status": "restarted", "pid": 5678}`

### 2. Model Inventory
- **GET** `/api/models`  
  *Returns*: List of discovered models categorized by type.
- **POST** `/api/models/discover`  
  *Action*: Trigger an immediate scan of all runtime plugins.  
  *Returns*: `{"status": "completed", "models_discovered": 12}`

### 3. Monitoring & Diagnostics
- **GET** `/api/metrics`  
  *Returns*: GPU, VRAM, CPU, RAM, active connections, and latency metrics.
- **GET** `/api/logs`  
  *Query Parameters*: `service_id: Optional[str]`, `lines: int = 100`  
  *Returns*: Log lines.
- **POST** `/api/operations/backup`  
  *Returns*: `{"status": "success", "backup_file": "C:\\backups\\arm-backup-2026.zip"}`
- **POST** `/api/operations/restore`  
  *Body*: `{"backup_file": "C:\\backups\\arm-backup-2026.zip"}`  
  *Returns*: `{"status": "success"}`
- **POST** `/api/operations/benchmark`  
  *Returns*: Latency, TTFT, and tokens/sec for the active model.

---

## Command Line Interface (CLI)

The CLI is packaged as a Python console script entry point called `arm`.

```powershell
# Show overall status of services and resource consumption
arm status

# Control services
arm start <service-id>
arm stop <service-id>
arm restart <service-id>

# Run discovery
arm discover

# Perform operational tasks
arm backup
arm restore --file <path-to-zip>
arm diagnostics
```

---

## Plugin Contract

Every plugin must be a Python package inside the `plugins/` directory containing a subclass of `BasePlugin`.

```python
class BasePlugin:
    def __init__(self, db_conn):
        self.db = db_conn

    def name(self) -> str:
        """Unique plugin name (e.g., 'litellm')."""
        raise NotImplementedError

    def on_register(self):
        """Hook called when the plugin is loaded into the system."""
        pass

    def build_config(self) -> dict:
        """Generate configurations specific to this runtime."""
        raise NotImplementedError
```
