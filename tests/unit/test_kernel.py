import os
import tempfile
import pytest
import json
import sqlite3
from unittest.mock import MagicMock, patch
from typing import Any

from src.backend.app.domain.models import Service, ServiceStatus, ServiceCheckResult, Capability, CapabilityType
from src.backend.app.domain.event import HealthChangedEvent, ConfigUpdatedEvent
from src.backend.app.domain.command import StartServiceCommand, StopServiceCommand, DiscoverInventoryCommand, UpdateConfigCommand
from src.backend.app.domain.policy import PreventLiteLLMStopWithActiveRequestsPolicy, PolicyDecision
from src.backend.app.domain.kernel import ControlPlaneKernel
from src.backend.app.infrastructure.persistence import sqlite_db
from src.backend.app.infrastructure.persistence.sqlite_repositories import (
    SqliteServiceRepository,
    SqliteCapabilityRepository,
    SqliteSystemConfigRepository,
    SqliteSystemInventoryRepository,
    SqliteOperationalHistoryRepository
)
from src.backend.app.domain.plugin import RuntimePlugin

@pytest.fixture
def temp_db():
    # Setup temporary file for test database
    fd, path = tempfile.mkstemp()
    os.environ["ARM_DB_PATH"] = path
    sqlite_db.init_db()
    yield path
    os.close(fd)
    try:
        os.remove(path)
    except Exception:
        pass
    os.environ.pop("ARM_DB_PATH", None)

class MockTestPlugin(RuntimePlugin):
    def get_identifier(self) -> str:
        return "mock-test"
    def get_name(self) -> str:
        return "Mock Test Plugin"
    def get_version(self) -> str:
        return "0.1.0"
    def get_required_dependencies(self) -> list:
        return []
    def get_supported_os(self) -> list:
        return ["windows", "linux", "darwin"]
    def get_config_schema(self) -> dict:
        return {}
    def get_health_probes(self) -> list:
        return []
    def discover_capabilities(self) -> list:
        return []
    def generate_runtime_files(self, service: Service) -> None:
        pass
    def start_service(self, service: Service) -> int:
        return 9999
    def stop_service(self, service: Service) -> bool:
        return True
    def get_raw_checks(self, service: Service) -> ServiceCheckResult:
        return ServiceCheckResult(pid_running=True, port_responsive=True, api_responsive=True)
    def get_metrics(self, service: Service) -> Any:
        # returns metrics mock
        from src.backend.app.domain.models import ServiceMetrics
        return ServiceMetrics(cpu_utilization_pct=15.5, ram_used_bytes=1024*1024, vram_used_bytes=512*1024, gpu_utilization_pct=5.0)

def test_kernel_initialization(temp_db):
    s_repo = SqliteServiceRepository()
    c_repo = SqliteCapabilityRepository()
    cfg_repo = SqliteSystemConfigRepository()
    inv_repo = SqliteSystemInventoryRepository()
    hist_repo = SqliteOperationalHistoryRepository()

    kernel = ControlPlaneKernel(s_repo, c_repo, cfg_repo, inv_repo, hist_repo)
    
    # Assert subsystems are initialized
    assert kernel.service_registry is not None
    assert kernel.capability_registry is not None
    assert kernel.event_bus is not None
    assert kernel.command_bus is not None
    assert kernel.policy_engine is not None
    assert kernel.health_engine is not None
    assert kernel.workflow_engine is not None
    assert kernel.inventory_engine is not None

def test_command_bus_dispatch_and_policy_violation(temp_db):
    s_repo = SqliteServiceRepository()
    c_repo = SqliteCapabilityRepository()
    cfg_repo = SqliteSystemConfigRepository()
    inv_repo = SqliteSystemInventoryRepository()
    hist_repo = SqliteOperationalHistoryRepository()

    kernel = ControlPlaneKernel(s_repo, c_repo, cfg_repo, inv_repo, hist_repo)
    plugin = MockTestPlugin()
    kernel.service_registry.register_plugin(plugin)

    # 1. Setup litellm service
    litellm_service = Service(
        id="litellm",
        name="LiteLLM Gateway",
        type="mock-test",
        port=8000,
        status=ServiceStatus.RUNNING,
        pid=1234
    )
    kernel.service_registry.register_service(litellm_service)

    # Mock command block using active requests policy config
    cfg_repo.set("litellm_active_requests", "3")
    
    with pytest.raises(ValueError) as exc:
        kernel.command_bus.dispatch(StopServiceCommand(service_id="litellm"), kernel)
    
    assert "LiteLLM has 3 active request sessions" in str(exc.value)

    # Resolve active requests
    cfg_repo.set("litellm_active_requests", "0")
    
    # Stop command should succeed
    success = kernel.command_bus.dispatch(StopServiceCommand(service_id="litellm"), kernel)
    assert success is True
    
    service = kernel.service_registry.get_service("litellm")
    assert service.status == ServiceStatus.STOPPED

def test_operational_history_tracking(temp_db):
    s_repo = SqliteServiceRepository()
    c_repo = SqliteCapabilityRepository()
    cfg_repo = SqliteSystemConfigRepository()
    inv_repo = SqliteSystemInventoryRepository()
    hist_repo = SqliteOperationalHistoryRepository()

    kernel = ControlPlaneKernel(s_repo, c_repo, cfg_repo, inv_repo, hist_repo)

    # Manually publish events and check history repository
    kernel.event_bus.publish(ConfigUpdatedEvent(key="timeout", value="30"))
    
    history_events = hist_repo.get_recent()
    assert len(history_events) >= 1
    assert history_events[0]["event_type"] == "CONFIG_UPDATE"
    assert history_events[0]["details"]["key"] == "timeout"
    assert history_events[0]["details"]["value"] == "30"

def test_auto_restart_policy_reactive(temp_db):
    s_repo = SqliteServiceRepository()
    c_repo = SqliteCapabilityRepository()
    cfg_repo = SqliteSystemConfigRepository()
    inv_repo = SqliteSystemInventoryRepository()
    hist_repo = SqliteOperationalHistoryRepository()

    kernel = ControlPlaneKernel(s_repo, c_repo, cfg_repo, inv_repo, hist_repo)
    plugin = MockTestPlugin()
    kernel.service_registry.register_plugin(plugin)

    service = Service(
        id="mock-test",
        name="Mock test",
        type="mock-test",
        port=5555,
        status=ServiceStatus.RUNNING,
        pid=1111
    )
    kernel.service_registry.register_service(service)

    # Set retry configuration
    cfg_repo.set("auto_restart_enabled", "true")
    cfg_repo.set("auto_restart_limit", "2")

    # Simulate transition from RUNNING -> ERROR unexpectedly
    kernel.event_bus.publish(HealthChangedEvent(
        service_id="mock-test",
        old_status="RUNNING",
        new_status="ERROR"
    ))

    # Verification: Should have dispatched StartServiceCommand.
    # Check that service status went back to RUNNING or update history shows restart logs.
    recent_history = hist_repo.get_recent()
    restart_logs = [h for h in recent_history if h["event_type"] == "SERVICE_RESTART"]
    assert len(restart_logs) >= 1
    assert "attempt 1/2" in restart_logs[0]["message"]

def test_expanded_inventory_scans(temp_db):
    s_repo = SqliteServiceRepository()
    c_repo = SqliteCapabilityRepository()
    cfg_repo = SqliteSystemConfigRepository()
    inv_repo = SqliteSystemInventoryRepository()
    hist_repo = SqliteOperationalHistoryRepository()

    kernel = ControlPlaneKernel(s_repo, c_repo, cfg_repo, inv_repo, hist_repo)
    
    # Run inventory scan
    kernel.inventory_engine.discover_and_populate()

    # Query inventory repo for standard elements
    python_item = inv_repo.get("python")
    assert python_item is not None
    assert python_item["category"] == "runtime"
    assert "version" in python_item["value"]

    ports_item = inv_repo.get("ports")
    assert ports_item is not None
    assert "in_use" in ports_item["value"]

def test_metrics_collection_persistence(temp_db):
    s_repo = SqliteServiceRepository()
    c_repo = SqliteCapabilityRepository()
    cfg_repo = SqliteSystemConfigRepository()
    inv_repo = SqliteSystemInventoryRepository()
    hist_repo = SqliteOperationalHistoryRepository()

    kernel = ControlPlaneKernel(s_repo, c_repo, cfg_repo, inv_repo, hist_repo)
    plugin = MockTestPlugin()
    kernel.service_registry.register_plugin(plugin)

    service = Service(
        id="mock-test",
        name="Mock active",
        type="mock-test",
        port=9999,
        status=ServiceStatus.RUNNING,
        pid=12345
    )
    kernel.service_registry.register_service(service)

    # Initialize MetricsEngine and collect metrics
    from src.backend.app.engine.metrics import MetricsEngine
    metrics_engine = MetricsEngine(kernel.service_registry, hist_repo)
    metrics_engine.collect_metrics()

    # Query SQLite performance_metrics table directly to confirm record
    conn = sqlite_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM performance_metrics WHERE service_id = 'mock-test';")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0]["cpu_utilization_pct"] == 15.5
    assert rows[0]["ram_used_bytes"] == 1024*1024
    assert rows[0]["vram_used_bytes"] == 512*1024
    assert rows[0]["gpu_utilization_pct"] == 5.0
