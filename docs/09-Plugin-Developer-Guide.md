# ForgeOps Plugin Developer Guide

ForgeOps features an extensible plugin framework that allows developers to add support for new local AI runtime engines (e.g., vLLM, KoboldCPP, Llama.cpp) without modifying the orchestrator core. 

This guide details how to develop, test, and register a custom runtime plugin.

---

## 1. Plugin Architecture

Every plugin must inherit from the abstract base class `RuntimePlugin` located in [plugin.py](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/src/backend/app/domain/plugin.py):

```python
from src.backend.app.domain.plugin import RuntimePlugin
```

### Plugin Lifecycle
1. **Discovery**: On application lifespan boot, plugins are loaded and instantiated in `main.py`.
2. **Registration**: The plugin instance is registered in the kernel's `ServiceRegistry`:
   ```python
   kernel.service_registry.register_plugin(MyCustomPlugin())
   ```
3. **Execution**: The database is queried for service matching the plugin identifier.
4. **Operations**: The plugin generates configs, starts processes, polls health telemetry, collects metrics, and stops processes.

---

## 2. API Method Interface Reference

To implement a valid plugin, you must implement the following 12 methods:

### Metadata & Dependencies
* `get_identifier(self) -> str`: Return a unique string token for the plugin (e.g., `"vllm"`). This maps directly to the `type` column in the SQLite `services` table.
* `get_name(self) -> str`: Return a user-friendly name (e.g., `"vLLM Orchestration Engine"`).
* `get_version(self) -> str`: Return the plugin's semver string (e.g., `"1.0.0"`).
* `get_required_dependencies(self) -> List[str]`: Return list of binary names required in the system path (e.g., `["python", "vllm"]`).
* `get_supported_os(self) -> List[str]`: Return operating systems supported (e.g. `["windows", "linux"]`).
* `get_config_schema(self) -> Dict[str, Any]`: Return a JSON schema dictionary for input validation.

### Configuration & Discovery
* `discover_capabilities(self) -> List[Capability]`: Query the local runtime APIs and return active model capabilities as a list of `Capability` objects.
* `generate_runtime_files(self, service: Service) -> None`: Generate any YAML, JSON, or configuration assets needed to run the service based on current settings.

### Service Lifecycle Controls
* `start_service(self, service: Service) -> int`: Launch the runtime subprocess. Return the process PID.
* `stop_service(self, service: Service) -> bool`: Stop the subprocess (returns `True` on success).
* `get_raw_checks(self, service: Service) -> ServiceCheckResult`: Execute http/tcp probes and verify if:
  * The PID is running.
  * The listening port responds.
  * The system API yields 200 OK.
* `get_metrics(self, service: Service) -> ServiceMetrics`: Collect CPU and RAM utilization for the process.

---

## 3. Step-by-Step Implementation Example

Here is a template implementation for a mock runtime plugin `vLLMPlugin` (saved to `src/backend/app/plugins/vllm.py`):

```python
import os
import httpx
import logging
from typing import List, Dict, Any
from src.backend.app.domain.models import Service, Capability, ServiceMetrics, CapabilityType, ServiceCheckResult
from src.backend.app.domain.plugin import RuntimePlugin
from src.backend.app.infrastructure import process_manager

logger = logging.getLogger("plugin.vllm")

class VllmPlugin(RuntimePlugin):
    def get_identifier(self) -> str:
        return "vllm"

    def get_name(self) -> str:
        return "vLLM Engine Plugin"

    def get_version(self) -> str:
        return "1.0.0"

    def get_required_dependencies(self) -> List[str]:
        return ["python"]

    def get_supported_os(self) -> List[str]:
        return ["windows", "linux"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "port": {"type": "integer", "default": 8000},
                "args": {"type": "array", "items": {"type": "string"}}
            }
        }

    def get_health_probes(self) -> List[Dict[str, Any]]:
        return [{"type": "http", "path": "/v1/models", "port": 8000}]

    def discover_capabilities(self) -> List[Capability]:
        # Implementation queries vLLM REST model listing
        return [
            Capability(
                id="vllm/meta-llama-3",
                name="meta-llama-3",
                type=CapabilityType.MODEL,
                provider="vllm",
                metadata={"family": "llama"}
            )
        ]

    def generate_runtime_files(self, service: Service) -> None:
        # Generate any config files if needed before launching
        pass

    def start_service(self, service: Service) -> int:
        binary = "python"
        args = ["-m", "vllm.entrypoints.openai.api_server", "--port", str(service.port or 8000)]
        pid = process_manager.start_process(binary, args)
        return pid

    def stop_service(self, service: Service) -> bool:
        if service.pid:
            return process_manager.stop_process(service.pid)
        return True

    def get_raw_checks(self, service: Service) -> ServiceCheckResult:
        pid_running = service.pid and process_manager.is_process_running(service.pid)
        # Verify port responsiveness
        port_responsive = False
        try:
            with httpx.Client(timeout=1.0) as client:
                res = client.get(f"http://127.0.0.1:{service.port}/v1/models")
                port_responsive = (res.status_code == 200)
        except Exception:
            pass
        return ServiceCheckResult(
            pid_running=pid_running,
            port_responsive=port_responsive,
            api_responsive=port_responsive,
            raw_details={}
        )

    def get_metrics(self, service: Service) -> ServiceMetrics:
        if service.pid and process_manager.is_process_running(service.pid):
            met = process_manager.get_process_metrics(service.pid)
            return ServiceMetrics(cpu_utilization_pct=met["cpu_percent"], ram_used_bytes=met["memory_rss_bytes"])
        return ServiceMetrics(cpu_utilization_pct=0.0, ram_used_bytes=0)
```

---

## 4. Registering Your Plugin

To register the plugin:
1. Open [main.py](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/src/backend/app/main.py).
2. Import your plugin at the top of the file:
   ```python
   from src.backend.app.plugins.vllm import VllmPlugin
   ```
3. Locate the `lifespan` context manager function, and register the plugin instance in the kernel service registry:
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # ...
       # Register plugins with kernel registry
       kernel.service_registry.register_plugin(OllamaPlugin())
       kernel.service_registry.register_plugin(LiteLLMPlugin())
       kernel.service_registry.register_plugin(OpenClawPlugin())
       kernel.service_registry.register_plugin(McpPlugin())
       kernel.service_registry.register_plugin(VllmPlugin()) # <-- ADD THIS
       # ...
   ```
4. Insert a matching service profile entry in your SQLite database `services` table with the `id` and `type` fields set to `"vllm"`.

---

## 5. Plugin Best Practices
* **Robust Subprocess Handling**: Use the built-in [process_manager.py](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/src/backend/app/infrastructure/process_manager.py) wrapper for starting and stopping processes to ensure clean environment parameter injection and prevent zombie processes.
* **Non-Blocking Telemetry**: Ensure `get_raw_checks` and `discover_capabilities` use low timeout thresholds (e.g. `<= 2.0` seconds) to prevent blocking the orchestrator event loop during network timeouts.
