import os
import httpx
import logging
import yaml
from typing import List, Dict, Any, Optional
from src.backend.app.domain.models import Service, Capability, ServiceMetrics, CapabilityType, ServiceCheckResult
from src.backend.app.domain.plugin import RuntimePlugin
from src.backend.app.infrastructure import process_manager

logger = logging.getLogger("plugin.litellm")

class LiteLLMPlugin(RuntimePlugin):
    def get_identifier(self) -> str:
        return "litellm"

    def get_name(self) -> str:
        return "LiteLLM Gateway Plugin"

    def get_version(self) -> str:
        return "1.0.0"

    def get_required_dependencies(self) -> List[str]:
        return ["litellm"]

    def get_supported_os(self) -> List[str]:
        return ["windows", "linux", "darwin"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "port": {"type": "integer", "default": 8000},
                "config_path": {"type": "string"}
            }
        }

    def get_health_probes(self) -> List[Dict[str, Any]]:
        return [
            {"type": "http", "path": "/v1/models", "port": 8000}
        ]

    def _get_api_url(self, service: Optional[Service] = None) -> str:
        port = service.port if service and service.port else 8000
        return f"http://127.0.0.1:{port}"

    def discover_capabilities(self) -> List[Capability]:
        url = f"{self._get_api_url()}/v1/models"
        capabilities = []
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    for m in models:
                        model_id = m.get("id")
                        capabilities.append(Capability(
                            id=f"litellm/{model_id}",
                            name=model_id,
                            type=CapabilityType.MODEL,
                            provider="litellm",
                            metadata={
                                "owned_by": m.get("owned_by"),
                                "object": m.get("object")
                            }
                        ))
        except httpx.RequestError as e:
            logger.warning(f"Could not connect to LiteLLM to discover models: {e}")
        return capabilities

    def generate_runtime_files(self, service: Service) -> None:
        """Generates the LiteLLM config.yaml proxy settings dynamically if missing."""
        if not service.config_path:
            # Set default path in program data or local workspace
            service.config_path = "litellm_config.yaml"

        directory = os.path.dirname(service.config_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        if not os.path.exists(service.config_path):
            logger.info(f"Generating declarative LiteLLM config file at: {service.config_path}")
            default_config = {
                "model_list": [
                    {
                        "model_name": "ollama-llama3",
                        "litellm_params": {
                            "model": "ollama/llama3",
                            "api_base": "http://localhost:11434"
                        }
                    }
                ],
                "litellm_settings": {
                    "drop_params": True
                }
            }
            try:
                with open(service.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(default_config, f, default_flow_style=False)
            except Exception as e:
                logger.error(f"Failed to dynamically write configuration files: {e}")

    def start_service(self, service: Service) -> int:
        # Dynamically generate configuration files first
        self.generate_runtime_files(service)

        binary = service.binary_path if service.binary_path else "litellm"
        port = service.port if service.port else 8000
        
        args = service.args.copy() if service.args else []
        if "--port" not in args and "-p" not in args:
            args.extend(["--port", str(port)])
        if "--config" not in args and "-c" not in args and service.config_path:
            args.extend(["--config", service.config_path])
        if "--host" not in args:
            args.extend(["--host", "127.0.0.1"])
            
        pid = process_manager.start_process(binary, args)
        return pid

    def stop_service(self, service: Service) -> bool:
        if service.pid:
            return process_manager.stop_process(service.pid)
        return True

    def get_raw_checks(self, service: Service) -> ServiceCheckResult:
        pid_running = False
        if service.pid and process_manager.is_process_running(service.pid):
            pid_running = True
            
        port_responsive = False
        api_responsive = False
        
        url = f"{self._get_api_url(service)}/v1/models"
        try:
            with httpx.Client(timeout=1.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    port_responsive = True
                    api_responsive = True
        except httpx.RequestError:
            pass
            
        return ServiceCheckResult(
            pid_running=pid_running,
            port_responsive=port_responsive,
            api_responsive=api_responsive,
            raw_details={}
        )

    def get_metrics(self, service: Service) -> ServiceMetrics:
        if service.pid and process_manager.is_process_running(service.pid):
            metrics_dict = process_manager.get_process_metrics(service.pid)
            return ServiceMetrics(
                cpu_utilization_pct=metrics_dict["cpu_percent"],
                ram_used_bytes=metrics_dict["memory_rss_bytes"]
            )
        return ServiceMetrics(cpu_utilization_pct=0.0, ram_used_bytes=0)
