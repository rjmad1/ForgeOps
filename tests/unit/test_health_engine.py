import pytest
from src.backend.app.domain.models import Service, ServiceStatus, ServiceCheckResult
from src.backend.app.domain.event import EventBus, HealthChangedEvent
from src.backend.app.engine.health import HealthEngine

class MemoryServiceRepository:
    def __init__(self):
        self.saved_service = None
    def save(self, service: Service):
        self.saved_service = service

def test_health_evaluation_stopped():
    bus = EventBus()
    repo = MemoryServiceRepository()
    engine = HealthEngine(bus, repo)

    service = Service(
        id="ollama",
        name="Ollama",
        type="ollama",
        port=11434,
        status=ServiceStatus.RUNNING
    )
    
    # Process is dead, port dead
    check = ServiceCheckResult(
        pid_running=False,
        port_responsive=False,
        api_responsive=False
    )
    
    new_status = engine.evaluate_and_update(service, check)
    assert new_status == ServiceStatus.STOPPED
    assert repo.saved_service.status == ServiceStatus.STOPPED
    assert repo.saved_service.pid is None

def test_health_evaluation_running():
    bus = EventBus()
    repo = MemoryServiceRepository()
    engine = HealthEngine(bus, repo)

    service = Service(
        id="litellm",
        name="LiteLLM",
        type="litellm",
        port=8000,
        status=ServiceStatus.STOPPED,
        pid=123
    )
    
    # Process running, port active, API active
    check = ServiceCheckResult(
        pid_running=True,
        port_responsive=True,
        api_responsive=True
    )
    
    new_status = engine.evaluate_and_update(service, check)
    assert new_status == ServiceStatus.RUNNING

def test_health_evaluation_degraded():
    bus = EventBus()
    repo = MemoryServiceRepository()
    engine = HealthEngine(bus, repo)

    service = Service(
        id="litellm",
        name="LiteLLM",
        type="litellm",
        port=8000,
        status=ServiceStatus.RUNNING,
        pid=123
    )
    
    # Port active, but API is failing
    check = ServiceCheckResult(
        pid_running=True,
        port_responsive=True,
        api_responsive=False
    )
    
    new_status = engine.evaluate_and_update(service, check)
    assert new_status == ServiceStatus.DEGRADED

def test_health_event_broadcasting():
    bus = EventBus()
    repo = MemoryServiceRepository()
    engine = HealthEngine(bus, repo)

    events = []
    bus.subscribe(HealthChangedEvent, lambda e: events.append(e))

    service = Service(
        id="openclaw",
        name="OpenClaw",
        type="openclaw",
        port=8080,
        status=ServiceStatus.RUNNING,
        pid=456
    )
    
    # Process dies
    check = ServiceCheckResult(
        pid_running=False,
        port_responsive=False,
        api_responsive=False
    )
    
    engine.evaluate_and_update(service, check)
    assert len(events) == 1
    assert events[0].service_id == "openclaw"
    assert events[0].old_status == "RUNNING"
    assert events[0].new_status == "STOPPED"
