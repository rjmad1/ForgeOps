import time
import pytest
from unittest.mock import MagicMock
from src.backend.app.domain.models import Service, ServiceStatus, ServiceCheckResult
from src.backend.app.domain.event import HealthChangedEvent
from src.backend.app.domain.command import StartServiceCommand, StopServiceCommand, RestartServiceCommand
from src.backend.app.domain.policy import PolicyEngine, PolicyDecision

class MockConfigRepo:
    def __init__(self, configs=None):
        self.configs = configs or {}
    def get(self, key):
        return self.configs.get(key)

class MockHistoryRepo:
    def __init__(self):
        self.logs = []
    def log(self, event_type, severity, message, service_id=None, details=None):
        self.logs.append({
            "event_type": event_type,
            "severity": severity,
            "message": message,
            "service_id": service_id,
            "details": details
        })

class MockCommandBus:
    def __init__(self):
        self.dispatched = []
    def set_policy_engine(self, policy_engine):
        pass
    def dispatch(self, command, kernel):
        self.dispatched.append(command)

class MockServiceRegistry:
    def __init__(self, service):
        self.service = service
    def get_service(self, service_id):
        return self.service

class MockKernel:
    def __init__(self, service, configs=None):
        self.config_repo = MockConfigRepo(configs)
        self.history_repo = MockHistoryRepo()
        self.command_bus = MockCommandBus()
        self.service_registry = MockServiceRegistry(service)

def test_auto_restart_flow():
    # Setup service and kernel
    service = Service(
        id="litellm",
        name="LiteLLM",
        type="litellm",
        status=ServiceStatus.STOPPED,
        port=8000
    )
    
    configs = {
        "auto_restart_enabled": "true",
        "auto_restart_limit": "2",
        "auto_restart_base_delay": "0.1",
        "auto_restart_max_delay": "1.0",
        "auto_restart_multiplier": "2.0",
        "auto_restart_jitter_pct": "0.0",
        "auto_restart_cooldown": "5.0",
        "auto_restart_window": "10.0"
    }
    
    kernel = MockKernel(service, configs)
    engine = PolicyEngine()
    
    # 1. Start service manually - resets and records healthy state
    cmd = StartServiceCommand(service_id="litellm")
    decision = engine.evaluate(cmd, kernel)
    assert decision.allowed is True
    assert engine._retry_counts["litellm"] == 0
    assert engine._circuit_breakers["litellm"] == "CLOSED"
    assert "litellm" in engine._healthy_since
    
    # Transition to RUNNING
    engine.handle_health_change(HealthChangedEvent(
        service_id="litellm",
        old_status="STOPPED",
        new_status="RUNNING"
    ), kernel)
    
    # 2. First failure (RUNNING -> ERROR)
    engine.handle_health_change(HealthChangedEvent(
        service_id="litellm",
        old_status="RUNNING",
        new_status="ERROR"
    ), kernel)
    
    assert engine._retry_counts["litellm"] == 1
    # Check that a thread was started and it dispatches start command
    time.sleep(0.2) # wait for the base delay (0.1s) plus some processing time
    assert len(kernel.command_bus.dispatched) == 1
    assert isinstance(kernel.command_bus.dispatched[0], StartServiceCommand)
    
    # Mark service running again after restart
    engine.handle_health_change(HealthChangedEvent(
        service_id="litellm",
        old_status="ERROR",
        new_status="RUNNING"
    ), kernel)
    
    # 3. Second failure (RUNNING -> STOPPED)
    engine.handle_health_change(HealthChangedEvent(
        service_id="litellm",
        old_status="RUNNING",
        new_status="STOPPED"
    ), kernel)
    
    assert engine._retry_counts["litellm"] == 2
    time.sleep(0.35) # exponential delay: 0.1 * 2^1 = 0.2s delay
    assert len(kernel.command_bus.dispatched) == 2
    
    # Mark running again
    engine.handle_health_change(HealthChangedEvent(
        service_id="litellm",
        old_status="STOPPED",
        new_status="RUNNING"
    ), kernel)
    
    # 4. Third failure (limit is 2, so this should trip Circuit Breaker to OPEN)
    engine.handle_health_change(HealthChangedEvent(
        service_id="litellm",
        old_status="RUNNING",
        new_status="ERROR"
    ), kernel)
    
    assert engine._circuit_breakers["litellm"] == "OPEN"
    # No additional dispatch because CB is open
    time.sleep(0.1)
    assert len(kernel.command_bus.dispatched) == 2
    
    # Check history error logged
    errors = [log for log in kernel.history_repo.logs if log["severity"] == "ERROR"]
    assert len(errors) == 1
    assert "auto-restart limit" in errors[0]["message"]
    
    # 5. Manual start command should close Circuit Breaker
    cmd = StartServiceCommand(service_id="litellm")
    decision = engine.evaluate(cmd, kernel)
    assert decision.allowed is True
    assert engine._circuit_breakers["litellm"] == "CLOSED"
    assert engine._retry_counts["litellm"] == 0

def test_cooldown_reset():
    service = Service(
        id="litellm",
        name="LiteLLM",
        type="litellm",
        status=ServiceStatus.STOPPED,
        port=8000
    )
    configs = {
        "auto_restart_enabled": "true",
        "auto_restart_limit": "2",
        "auto_restart_base_delay": "0.01",
        "auto_restart_cooldown": "0.2"
    }
    kernel = MockKernel(service, configs)
    engine = PolicyEngine()
    
    # Initialize running
    engine.handle_health_change(HealthChangedEvent(
        service_id="litellm",
        old_status="STOPPED",
        new_status="RUNNING"
    ), kernel)
    
    # Fail
    engine.handle_health_change(HealthChangedEvent(
        service_id="litellm",
        old_status="RUNNING",
        new_status="ERROR"
    ), kernel)
    assert engine._retry_counts["litellm"] == 1
    
    # Running again, then sleep longer than cooldown (0.2s)
    engine.handle_health_change(HealthChangedEvent(
        service_id="litellm",
        old_status="ERROR",
        new_status="RUNNING"
    ), kernel)
    
    time.sleep(0.25)
    
    # Fail again, should reset retries
    engine.handle_health_change(HealthChangedEvent(
        service_id="litellm",
        old_status="RUNNING",
        new_status="ERROR"
    ), kernel)
    
    assert engine._retry_counts["litellm"] == 1 # reset to 0, then incremented to 1
