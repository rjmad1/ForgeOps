import pytest
import socket
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

from src.backend.app.domain.models import Service, ServiceStatus, Capability
from src.backend.app.domain.workflow import Workflow, WorkflowStep
from src.backend.app.domain.registry import ServiceRegistry, CapabilityRegistry
from src.backend.app.engine.health import HealthEngine
from src.backend.app.engine.workflow_engine import WorkflowEngine, PreFlightCheckStep

class MemoryServiceRepository:
    def __init__(self):
        self.db = {}
    def save(self, service: Service):
        self.db[service.id] = service
    def get_by_id(self, service_id: str):
        return self.db.get(service_id)
    def get_all(self):
        return list(self.db.values())

class MemoryCapabilityRepository:
    def __init__(self):
        self.db = {}
    def save(self, capability: Capability):
        self.db[capability.id] = capability
    def clear_by_provider(self, provider: str):
        self.db = {k: v for k, v in self.db.items() if v.provider != provider}
    def get_all(self):
        return list(self.db.values())

# Mock Step to test rollback behaviour
class DummyStep(WorkflowStep):
    def __init__(self, name: str, should_fail: bool = False):
        self._name = name
        self.should_fail = should_fail
        self.executed = False
        self.rolled_back = False

    @property
    def name(self) -> str:
        return self._name

    def execute(self, context: Dict[str, Any]) -> None:
        self.executed = True
        if self.should_fail:
            raise RuntimeError(f"Step '{self._name}' forced failure")

    def rollback(self, context: Dict[str, Any]) -> None:
        self.rolled_back = True


def test_workflow_rollback_sequence():
    step1 = DummyStep("Step 1")
    step2 = DummyStep("Step 2", should_fail=True)
    step3 = DummyStep("Step 3")

    workflow = Workflow("Rollback Demo", [step1, step2, step3])
    context = {}

    success = workflow.execute(context)
    
    assert success is False
    assert step1.executed is True
    assert step1.rolled_back is True
    assert step2.executed is True
    assert step2.rolled_back is False  # Step that failed is not rolled back in default implementation or rolled back depending on code
    assert step3.executed is False
    assert step3.rolled_back is False


@patch("socket.socket")
def test_pre_flight_check_port_in_use(mock_socket):
    # Simulate port in use
    mock_instance = MagicMock()
    mock_instance.connect_ex.return_value = 0  # 0 indicates successful connection (port bound)
    mock_socket.return_value.__enter__.return_value = mock_instance

    step = PreFlightCheckStep()
    service = Service(
        id="ollama",
        name="Ollama",
        type="ollama",
        port=11434,
        status=ServiceStatus.STOPPED
    )
    context = {"service": service}

    with pytest.raises(IOError) as exc:
        step.execute(context)
    assert "already in use" in str(exc.value)


@patch("socket.socket")
def test_pre_flight_check_port_free(mock_socket):
    # Simulate port is free
    mock_instance = MagicMock()
    mock_instance.connect_ex.return_value = 111  # non-zero indicates connection failed (port free)
    mock_socket.return_value.__enter__.return_value = mock_instance

    step = PreFlightCheckStep()
    service = Service(
        id="ollama",
        name="Ollama",
        type="ollama",
        port=11434,
        status=ServiceStatus.STOPPED
    )
    context = {"service": service}

    # Should run fine without raising any error
    step.execute(context)
