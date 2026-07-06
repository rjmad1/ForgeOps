import os
import json
import logging
from typing import List, Dict, Any
from src.backend.app.domain.models import Service, Capability, ServiceMetrics, CapabilityType, ServiceCheckResult
from src.backend.app.domain.plugin import RuntimePlugin
from src.backend.app.infrastructure import process_manager

logger = logging.getLogger("plugin.mcp")

class McpPlugin(RuntimePlugin):
    def get_identifier(self) -> str:
        return "mcp"

    def get_name(self) -> str:
        return "Model Context Protocol Plugin"

    def get_version(self) -> str:
        return "1.0.0"

    def get_required_dependencies(self) -> List[str]:
        return []

    def get_supported_os(self) -> List[str]:
        return ["windows", "linux", "darwin"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mcp_servers": {"type": "object"}
            }
        }

    def get_health_probes(self) -> List[Dict[str, Any]]:
        return []

    def _get_mcp_config_path(self) -> str:
        app_data = os.environ.get("APPDATA", "")
        return os.path.join(app_data, "Claude", "claude_desktop_config.json")

    def discover_capabilities(self) -> List[Capability]:
        capabilities = [
            Capability(
                id="mcp/protocol",
                name="Model Context Protocol Provider",
                type=CapabilityType.TOOL,
                provider="mcp",
                metadata={"description": "Supports tool-calling protocol endpoints"}
            )
        ]
        
        config_path = self._get_mcp_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    mcp_servers = config.get("mcpServers", {})
                    for server_name, server_cfg in mcp_servers.items():
                        capabilities.append(Capability(
                            id=f"mcp/server/{server_name}",
                            name=server_name,
                            type=CapabilityType.TOOL,
                            provider="mcp",
                            metadata={
                                "command": server_cfg.get("command"),
                                "args": server_cfg.get("args", []),
                                "env": server_cfg.get("env", {})
                            }
                        ))
            except Exception as e:
                logger.error(f"Error reading Claude Desktop MCP config: {e}")
                
        return capabilities

    def generate_runtime_files(self, service: Service) -> None:
        pass

    def start_service(self, service: Service) -> int:
        if not service.binary_path:
            logger.warning("MCP service does not define a binary_path; skipping startup.")
            return 0
        pid = process_manager.start_process(service.binary_path, service.args)
        return pid

    def stop_service(self, service: Service) -> bool:
        if service.pid:
            return process_manager.stop_process(service.pid)
        return True

    def get_raw_checks(self, service: Service) -> ServiceCheckResult:
        pid_running = False
        if service.pid and process_manager.is_process_running(service.pid):
            pid_running = True
            
        return ServiceCheckResult(
            pid_running=pid_running,
            port_responsive=False,
            api_responsive=False,
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
