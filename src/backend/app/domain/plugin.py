from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import Service, Capability, ServiceCheckResult, ServiceMetrics

class RuntimePlugin(ABC):
    @abstractmethod
    def get_identifier(self) -> str:
        """Returns the unique identifier for the plugin (e.g. 'ollama')."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Returns the human-readable name of the plugin."""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Returns the version of the plugin."""
        pass

    @abstractmethod
    def get_required_dependencies(self) -> List[str]:
        """Returns a list of executable/binary dependencies required by this plugin."""
        pass

    @abstractmethod
    def get_supported_os(self) -> List[str]:
        """Returns a list of supported operating systems (e.g., ['windows', 'linux'])."""
        pass

    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Returns a configuration schema description for configuration validation."""
        pass

    @abstractmethod
    def get_health_probes(self) -> List[Dict[str, Any]]:
        """Returns a list of health probes defined for the plugin."""
        pass

    @abstractmethod
    def discover_capabilities(self) -> List[Capability]:
        """Queries the runtime and returns its capabilities/models."""
        pass

    @abstractmethod
    def generate_runtime_files(self, service: Service) -> None:
        """Generates configuration files or runtime assets needed for execution from domain configurations."""
        pass

    @abstractmethod
    def start_service(self, service: Service) -> int:
        """Launches the service process and returns its PID."""
        pass

    @abstractmethod
    def stop_service(self, service: Service) -> bool:
        """Stops the service process."""
        pass

    @abstractmethod
    def get_raw_checks(self, service: Service) -> ServiceCheckResult:
        """Pulls raw checks telemetry (process alive, port connectivity, API responsiveness) from the host."""
        pass

    @abstractmethod
    def get_metrics(self, service: Service) -> ServiceMetrics:
        """Returns the performance/resource metrics for the service."""
        pass

