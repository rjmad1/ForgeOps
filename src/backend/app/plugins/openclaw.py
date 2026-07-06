import os
import httpx
import logging
from typing import List, Dict, Any, Optional
from src.backend.app.domain.models import Service, Capability, ServiceMetrics, CapabilityType, ServiceCheckResult
from src.backend.app.domain.plugin import RuntimePlugin
from src.backend.app.infrastructure import process_manager

logger = logging.getLogger("plugin.openclaw")

class OpenClawPlugin(RuntimePlugin):
    def get_identifier(self) -> str:
        return "openclaw"

    def get_name(self) -> str:
        return "OpenClaw Supervisor Plugin"

    def get_version(self) -> str:
        return "1.0.0"

    def get_required_dependencies(self) -> List[str]:
        return ["openclaw"]

    def get_supported_os(self) -> List[str]:
        return ["windows", "linux", "darwin"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "port": {"type": "integer", "default": 8080}
            }
        }

    def get_health_probes(self) -> List[Dict[str, Any]]:
        return [
            {"type": "http", "path": "/health", "port": 8080}
        ]

    def _get_api_url(self, service: Optional[Service] = None) -> str:
        port = service.port if service and service.port else 8080
        return f"http://127.0.0.1:{port}"

    def discover_capabilities(self) -> List[Capability]:
        capabilities = [
            Capability(
                id="openclaw/runner",
                name="OpenClaw Agent Runner",
                type=CapabilityType.AGENT_RUNNER,
                provider="openclaw",
                metadata={"description": "Orchestrates multi-agent openclaw tasks"}
            )
        ]
        
        url = f"{self._get_api_url()}/api/agents"
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    agents = data.get("agents", [])
                    for agent in agents:
                        agent_name = agent.get("name")
                        capabilities.append(Capability(
                            id=f"openclaw/agent/{agent_name}",
                            name=agent_name,
                            type=CapabilityType.AGENT_RUNNER,
                            provider="openclaw",
                            metadata={
                                "description": agent.get("description"),
                                "tools": agent.get("tools", [])
                            }
                        ))
        except httpx.RequestError:
            pass
            
        return capabilities

    def generate_runtime_files(self, service: Service) -> None:
        pass

    def start_service(self, service: Service) -> int:
        binary = service.binary_path if service.binary_path else "openclaw"
        args = service.args if service.args else []
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
        
        url = f"{self._get_api_url(service)}/health"
        try:
            with httpx.Client(timeout=1.0) as client:
                response = client.get(url)
                if response.status_code in [200, 404]:
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
