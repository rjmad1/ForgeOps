import logging
from src.backend.app.domain.models import Service, ServiceStatus, ServiceCheckResult
from src.backend.app.domain.event import EventBus, HealthChangedEvent
from src.backend.app.domain.repositories import ServiceRepository

logger = logging.getLogger("engine.health")

class HealthEngine:
    def __init__(self, event_bus: EventBus, service_repository: ServiceRepository):
        self.event_bus = event_bus
        self.repository = service_repository

    def evaluate_and_update(self, service: Service, check_result: ServiceCheckResult) -> ServiceStatus:
        """Evaluates raw checks telemetry against state rules, updates DB, and broadcasts event on change."""
        old_status = service.status
        new_status = self.evaluate_status(service, check_result)
        
        if old_status != new_status:
            service.status = new_status
            if new_status == ServiceStatus.STOPPED:
                service.pid = None
            self.repository.save(service)
            
            logger.info(f"Health state change: Service '{service.id}' transitioned from {old_status.value} -> {new_status.value}")
            self.event_bus.publish(HealthChangedEvent(
                service_id=service.id,
                old_status=old_status.value,
                new_status=new_status.value
            ))
            
        return new_status

    def evaluate_status(self, service: Service, check: ServiceCheckResult) -> ServiceStatus:
        """Assigns service status based on raw check parameters."""
        # Transitional statuses are managed by workflow engine, bypass active re-evaluation
        if service.status in [ServiceStatus.STARTING, ServiceStatus.CONFIGURING, ServiceStatus.UPDATING]:
            return service.status
            
        if not check.pid_running:
            # If the process was started externally or configured without local control
            if check.port_responsive or check.api_responsive:
                return ServiceStatus.RUNNING
            return ServiceStatus.STOPPED

        # Process is running locally
        if service.port is not None:
            if check.port_responsive and check.api_responsive:
                return ServiceStatus.RUNNING
            elif check.port_responsive or check.api_responsive:
                return ServiceStatus.DEGRADED
            else:
                return ServiceStatus.ERROR
        else:
            # Service has no port mapping (e.g. stdio-based MCP servers)
            return ServiceStatus.RUNNING if check.pid_running else ServiceStatus.STOPPED
