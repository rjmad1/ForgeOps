import os
import httpx
import logging
from typing import List, Dict, Any, Optional
from src.backend.app.domain.models import Service, Capability, ServiceMetrics, CapabilityType, ServiceCheckResult
from src.backend.app.domain.plugin import RuntimePlugin
from src.backend.app.infrastructure import process_manager

logger = logging.getLogger("plugin.ollama")

class OllamaPlugin(RuntimePlugin):
    def get_identifier(self) -> str:
        return "ollama"

    def get_name(self) -> str:
        return "Ollama Daemon Plugin"

    def get_version(self) -> str:
        return "1.0.0"

    def get_required_dependencies(self) -> List[str]:
        return ["ollama"]

    def get_supported_os(self) -> List[str]:
        return ["windows", "linux", "darwin"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "port": {"type": "integer", "default": 11434},
                "args": {"type": "array", "items": {"type": "string"}}
            }
        }

    def get_health_probes(self) -> List[Dict[str, Any]]:
        return [
            {"type": "http", "path": "/api/tags", "port": 11434}
        ]

    def _get_api_url(self, service: Optional[Service] = None) -> str:
        port = service.port if service and service.port else 11434
        return f"http://127.0.0.1:{port}"

    def discover_capabilities(self) -> List[Capability]:
        url = f"{self._get_api_url()}/api/tags"
        capabilities = []
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    for m in models:
                        name = m.get("name")
                        details = m.get("details", {})
                        capabilities.append(Capability(
                            id=f"ollama/{name}",
                            name=name,
                            type=CapabilityType.MODEL,
                            provider="ollama",
                            metadata={
                                "size_bytes": m.get("size"),
                                "family": details.get("family"),
                                "parameter_size": details.get("parameter_size"),
                                "quantization_level": details.get("quantization_level"),
                                "format": details.get("format")
                            }
                        ))
        except httpx.RequestError as e:
            logger.warning(f"Could not connect to Ollama to discover models: {e}")
        return capabilities

    def generate_runtime_files(self, service: Service) -> None:
        pass

    def start_service(self, service: Service) -> int:
        binary = service.binary_path
        if not binary:
            local_app_data = os.environ.get("LOCALAPPDATA", "")
            program_files = os.environ.get("ProgramFiles", "")
            paths = [
                os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe"),
                os.path.join(program_files, "Ollama", "ollama.exe"),
                "ollama"
            ]
            for p in paths:
                if p == "ollama" or os.path.exists(p):
                    binary = p
                    break
            
            if not binary:
                binary = "ollama"

        args = service.args if service.args else ["serve"]
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
        
        url = f"{self._get_api_url(service)}/api/tags"
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
