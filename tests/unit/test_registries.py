import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

from src.backend.app.domain.models import Service, Capability, ServiceStatus, ServiceMetrics, CapabilityType, ServiceCheckResult
from src.backend.app.domain.plugin import RuntimePlugin
from src.backend.app.domain.registry import ServiceRegistry, CapabilityRegistry
from src.backend.app.engine.inventory import InventoryEngine

# In-memory repositories for clean domain testing
class MemoryServiceRepository:
    def __init__(self):
        self.db = {}
    def save(self, service: Service):
        self.db[service.id] = service
    def get_by_id(self, service_id: str):
        return self.db.get(service_id)
    def get_all(self):
        return list(self.db.values())
    def delete(self, service_id: str):
        self.db.pop(service_id, None)

class MemoryCapabilityRepository:
    def __init__(self):
        self.db = {}
    def save(self, capability: Capability):
        self.db[capability.id] = capability
    def get_by_id(self, capability_id: str):
        return self.db.get(capability_id)
    def get_all(self):
        return list(self.db.values())
    def get_by_provider(self, provider: str):
        return [c for c in self.db.values() if c.provider == provider]
    def delete(self, capability_id: str):
        self.db.pop(capability_id, None)
    def clear_all(self):
        self.db.clear()
    def clear_by_provider(self, provider: str):
        self.db = {k: v for k, v in self.db.items() if v.provider != provider}

# Mock plugin for testing
class MockPlugin(RuntimePlugin):
    def __init__(self, identifier: str = "mock-plugin"):
        self.identifier = identifier
        self.started = False
        self.stopped = False

    def get_identifier(self) -> str:
        return self.identifier

    def get_name(self) -> str:
        return "Mock Plugin"

    def get_version(self) -> str:
        return "1.0.0"

    def get_required_dependencies(self) -> List[str]:
        return []

    def get_supported_os(self) -> List[str]:
        return ["windows", "linux", "darwin"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_health_probes(self) -> List[Dict[str, Any]]:
        return []

    def discover_capabilities(self) -> List[Capability]:
        return [
            Capability(
                id=f"{self.identifier}/model-1",
                name="model-1",
                type=CapabilityType.MODEL,
                provider=self.identifier,
                metadata={"size_bytes": 100}
            )
        ]

    def generate_runtime_files(self, service: Service) -> None:
        pass

    def start_service(self, service: Service) -> int:
        self.started = True
        return 12345

    def stop_service(self, service: Service) -> bool:
        self.stopped = True
        return True

    def get_raw_checks(self, service: Service) -> ServiceCheckResult:
        return ServiceCheckResult(
            pid_running=self.started,
            port_responsive=self.started,
            api_responsive=self.started
        )

    def get_metrics(self, service: Service) -> ServiceMetrics:
        return ServiceMetrics(cpu_utilization_pct=10.0, ram_used_bytes=5000)


def test_service_registry_lifecycle():
    repo = MemoryServiceRepository()
    registry = ServiceRegistry(repo)
    plugin = MockPlugin()
    
    registry.register_plugin(plugin)
    
    # Verify plugin registration
    assert registry.get_plugin("mock-plugin") == plugin
    assert len(registry.list_plugins()) == 1
    
    # Save a service config
    service = Service(
        id="mock-plugin",
        name="Mock Service",
        type="mock-plugin",
        port=5555,
        status=ServiceStatus.STOPPED
    )
    registry.register_service(service)
    
    # Retrieve and start service
    assert registry.get_service("mock-plugin").status == ServiceStatus.STOPPED
    
    success = registry.start_service("mock-plugin")
    assert success is True
    assert plugin.started is True
    
    # Service status in database should be updated
    db_service = registry.get_service("mock-plugin")
    assert db_service.status == ServiceStatus.RUNNING
    assert db_service.pid == 12345
    
    # Stop service
    success = registry.stop_service("mock-plugin")
    assert success is True
    assert plugin.stopped is True
    assert registry.get_service("mock-plugin").status == ServiceStatus.STOPPED


def test_capability_registry_refresh():
    s_repo = MemoryServiceRepository()
    c_repo = MemoryCapabilityRepository()
    
    s_registry = ServiceRegistry(s_repo)
    c_registry = CapabilityRegistry(c_repo)
    
    plugin = MockPlugin("ollama")
    s_registry.register_plugin(plugin)
    
    # Save active service definition so the refresh registers it as active/discoverable
    service = Service(id="ollama", name="Ollama", type="ollama", port=11434, status=ServiceStatus.RUNNING)
    s_registry.register_service(service)
    
    c_registry.refresh_capabilities(s_registry)
    
    caps = c_registry.list_capabilities()
    assert len(caps) == 1
    assert caps[0].id == "ollama/model-1"
    assert caps[0].provider == "ollama"


@patch("shutil.which")
def test_inventory_engine_discovery(mock_which):
    # Setup mock_which to find 'ollama' but not 'litellm'
    def side_effect(cmd):
        if cmd == "ollama":
            return "C:\\Windows\\System32\\ollama.exe"
        return None
    mock_which.side_effect = side_effect
    
    s_repo = MemoryServiceRepository()
    c_repo = MemoryCapabilityRepository()
    s_registry = ServiceRegistry(s_repo)
    c_registry = CapabilityRegistry(c_repo)
    
    ollama_plugin = MockPlugin("ollama")
    litellm_plugin = MockPlugin("litellm")
    s_registry.register_plugin(ollama_plugin)
    s_registry.register_plugin(litellm_plugin)
    
    engine = InventoryEngine(s_registry, c_registry)
    
    with patch("os.path.exists", return_value=False):
        engine.discover_and_populate()
        
    # Ollama is supported (found on path), so it should be registered
    assert s_registry.get_service("ollama") is not None
    # LiteLLM is not supported (not found on path), so it should NOT be registered
    assert s_registry.get_service("litellm") is None
    
    # Capabilities should be populated for registered service
    assert len(c_registry.get_capabilities_by_provider("ollama")) == 1
    assert len(c_registry.get_capabilities_by_provider("litellm")) == 0
