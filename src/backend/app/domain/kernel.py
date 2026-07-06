import logging
from typing import Any, Optional

from src.backend.app.domain.registry import ServiceRegistry, CapabilityRegistry
from src.backend.app.domain.event import (
    EventBus, HealthChangedEvent, ServiceStartedEvent, 
    ServiceStoppedEvent, ConfigUpdatedEvent, CapabilitiesRefreshedEvent
)
from src.backend.app.domain.command import (
    CommandBus, StartServiceCommand, StartServiceHandler,
    StopServiceCommand, StopServiceHandler,
    RestartServiceCommand, RestartServiceHandler,
    DiscoverInventoryCommand, DiscoverInventoryHandler,
    UpdateConfigCommand, UpdateConfigHandler
)
from src.backend.app.domain.policy import (
    PolicyEngine, PreventLiteLLMStopWithActiveRequestsPolicy, ModelPreferencePolicy
)
from src.backend.app.engine.health import HealthEngine
from src.backend.app.engine.workflow_engine import WorkflowEngine
from src.backend.app.engine.inventory import InventoryEngine

logger = logging.getLogger("domain.kernel")

class HistoryTracker:
    def __init__(self, event_bus: EventBus, history_repo: Any):
        self.event_bus = event_bus
        self.history_repo = history_repo

    def start(self) -> None:
        self.event_bus.subscribe(HealthChangedEvent, self.on_health_changed)
        self.event_bus.subscribe(ConfigUpdatedEvent, self.on_config_updated)
        self.event_bus.subscribe(ServiceStartedEvent, self.on_service_started)
        self.event_bus.subscribe(ServiceStoppedEvent, self.on_service_stopped)
        self.event_bus.subscribe(CapabilitiesRefreshedEvent, self.on_capabilities_refreshed)
        logger.info("HistoryTracker subscribed to all EventBus channels.")

    def on_health_changed(self, event: HealthChangedEvent) -> None:
        severity = "INFO"
        if event.new_status in ["ERROR", "DEGRADED"]:
            severity = "WARNING"
        self.history_repo.log(
            event_type="HEALTH_CHANGE",
            severity=severity,
            message=f"Service '{event.service_id}' health changed from {event.old_status} to {event.new_status}.",
            service_id=event.service_id,
            details={"old_status": event.old_status, "new_status": event.new_status}
        )

    def on_config_updated(self, event: ConfigUpdatedEvent) -> None:
        self.history_repo.log(
            event_type="CONFIG_UPDATE",
            severity="INFO",
            message=f"Configuration '{event.key}' updated to '{event.value}'.",
            details={"key": event.key, "value": event.value}
        )

    def on_service_started(self, event: ServiceStartedEvent) -> None:
        self.history_repo.log(
            event_type="WORKFLOW_EXECUTION",
            severity="INFO",
            message=f"Service '{event.service_id}' start workflow completed successfully (PID {event.pid}).",
            service_id=event.service_id,
            details={"pid": event.pid}
        )

    def on_service_stopped(self, event: ServiceStoppedEvent) -> None:
        self.history_repo.log(
            event_type="WORKFLOW_EXECUTION",
            severity="INFO",
            message=f"Service '{event.service_id}' stop workflow completed successfully.",
            service_id=event.service_id
        )

    def on_capabilities_refreshed(self, event: CapabilitiesRefreshedEvent) -> None:
        self.history_repo.log(
            event_type="PLUGIN_LIFECYCLE",
            severity="INFO",
            message=f"Refreshed {event.count} capabilities for provider '{event.provider}'.",
            details={"provider": event.provider, "count": event.count}
        )


class ControlPlaneKernel:
    def __init__(
        self,
        service_repo: Any,
        capability_repo: Any,
        config_repo: Any,
        inventory_repo: Any,
        history_repo: Any
    ):
        self.config_repo = config_repo
        self.inventory_repo = inventory_repo
        self.history_repo = history_repo

        # 1. Initialize Registries and core Event Bus
        self.event_bus = EventBus()
        self.service_registry = ServiceRegistry(service_repo)
        self.capability_registry = CapabilityRegistry(capability_repo)

        # 2. Initialize Engines
        self.health_engine = HealthEngine(self.event_bus, service_repo)
        self.workflow_engine = WorkflowEngine(
            self.service_registry, self.capability_registry, self.health_engine
        )
        # Inject event_bus to workflow engine so it can publish events
        self.workflow_engine.event_bus = self.event_bus

        self.inventory_engine = InventoryEngine(
            self.service_registry, self.capability_registry, self.health_engine, self.inventory_repo
        )

        # 3. Initialize Command Bus and Policy Engine
        self.command_bus = CommandBus()
        self.policy_engine = PolicyEngine()
        
        # Connect command bus and policy engine
        self.command_bus.set_policy_engine(self.policy_engine)

        # Register standard command handlers
        self.command_bus.register(StartServiceCommand, StartServiceHandler())
        self.command_bus.register(StopServiceCommand, StopServiceHandler())
        self.command_bus.register(RestartServiceCommand, RestartServiceHandler())
        self.command_bus.register(DiscoverInventoryCommand, DiscoverInventoryHandler())
        self.command_bus.register(UpdateConfigCommand, UpdateConfigHandler())

        # Register default policies
        self.policy_engine.register_policy(PreventLiteLLMStopWithActiveRequestsPolicy())
        self.policy_engine.register_policy(ModelPreferencePolicy())

        # Subscribe Policy Engine to Health Events for Auto-Restart
        self.event_bus.subscribe(HealthChangedEvent, lambda ev: self.policy_engine.handle_health_change(ev, self))

        # 4. Set up History Tracker
        self.history_tracker = HistoryTracker(self.event_bus, self.history_repo)
        self.history_tracker.start()

        # 5. Background Scheduler & Metrics Engine (Deferred to start() call)
        self.scheduler = None
        self.metrics_engine = None

    def start(self) -> None:
        """Starts background loops (Scheduler and Metrics Engine)."""
        logger.info("Starting Control Plane Kernel...")
        
        # Initialize Scheduler & Metrics dynamically to resolve circular dependency
        from src.backend.app.engine.scheduler import Scheduler
        from src.backend.app.engine.metrics import MetricsEngine

        self.metrics_engine = MetricsEngine(self.service_registry, self.history_repo)
        self.scheduler = Scheduler(self)
        self.scheduler.start()
        
        logger.info("Control Plane Kernel started successfully.")

    def stop(self) -> None:
        """Stops background loops and shuts down child runtimes gracefully."""
        logger.info("Stopping Control Plane Kernel...")
        if self.scheduler:
            self.scheduler.stop()
            
        # Shut down child runtimes gracefully to prevent zombie processes (IVV-OPS-01)
        try:
            for s in self.service_registry.list_services():
                if s.status.value in ["RUNNING", "STARTING", "DEGRADED", "UPDATING", "CONFIGURING"]:
                    logger.info(f"Gracefully stopping active service '{s.id}' during kernel stop...")
                    try:
                        self.workflow_engine.execute_stop_service(s.id)
                    except Exception as e:
                        logger.error(f"Failed to stop service '{s.id}' during kernel stop: {e}")
        except Exception as e:
            logger.error(f"Error listing services during kernel stop: {e}")
            
        logger.info("Control Plane Kernel stopped.")
