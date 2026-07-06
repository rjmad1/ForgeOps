import time
import socket
import logging
import platform
import os
from typing import Dict, Any
from src.backend.app.domain.models import Service, ServiceStatus, ServiceCheckResult
from src.backend.app.domain.workflow import Workflow, WorkflowStep
from src.backend.app.domain.registry import ServiceRegistry, CapabilityRegistry
from src.backend.app.engine.health import HealthEngine

logger = logging.getLogger("workflow.engine")

class PreFlightCheckStep(WorkflowStep):
    @property
    def name(self) -> str:
        return "Pre-flight Verification"

    def execute(self, context: Dict[str, Any]) -> None:
        service: Service = context["service"]
        plugin = context.get("plugin")
        
        # Compatibility checks (only run if plugin is registered in context)
        if plugin:
            # 1. Compatibility Check - Operating System
            system_os = platform.system().lower()
            supported_os = [o.lower() for o in plugin.get_supported_os()]
            if supported_os and system_os not in supported_os:
                raise ValueError(f"Plugin '{plugin.get_identifier()}' is not supported on OS '{system_os}'. Supported: {plugin.get_supported_os()}")

            # 2. Compatibility Check - Binary dependency availability
            for dep in plugin.get_required_dependencies():
                import shutil
                if not shutil.which(dep):
                    # Fallback check for Ollama in default windows paths
                    local_app_data = os.environ.get("LOCALAPPDATA", "")
                    program_files = os.environ.get("ProgramFiles", "")
                    p1 = os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe")
                    p2 = os.path.join(program_files, "Ollama", "ollama.exe")
                    if not (dep == "ollama" and (os.path.exists(p1) or os.path.exists(p2))):
                        raise FileNotFoundError(f"Missing required binary dependency '{dep}' for service '{service.id}'.")

        # 3. Port availability
        if service.port:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                # If connect_ex returns 0, the port is already bound (in use)
                if s.connect_ex(("127.0.0.1", service.port)) == 0:
                    raise IOError(f"Port {service.port} is already in use by another process.")
        logger.info("Pre-flight checks passed.")

    def rollback(self, context: Dict[str, Any]) -> None:
        pass


class UpdateStatusStep(WorkflowStep):
    def __init__(self, status: ServiceStatus, rollback_status: ServiceStatus):
        self._status = status
        self._rollback_status = rollback_status

    @property
    def name(self) -> str:
        return f"Update Status to {self._status.value}"

    def execute(self, context: Dict[str, Any]) -> None:
        service: Service = context["service"]
        registry: ServiceRegistry = context["service_registry"]
        service.status = self._status
        registry.register_service(service)

    def rollback(self, context: Dict[str, Any]) -> None:
        service: Service = context["service"]
        registry: ServiceRegistry = context["service_registry"]
        service.status = self._rollback_status
        service.pid = None
        registry.register_service(service)


class LaunchProcessStep(WorkflowStep):
    @property
    def name(self) -> str:
        return "Launch Subprocess"

    def execute(self, context: Dict[str, Any]) -> None:
        service: Service = context["service"]
        plugin = context["plugin"]
        registry: ServiceRegistry = context["service_registry"]
        
        pid = plugin.start_service(service)
        if pid <= 0:
            raise RuntimeError("Plugin failed to launch service executable.")
            
        context["pid"] = pid
        service.pid = pid
        registry.register_service(service)
        logger.info(f"Launched process with PID {pid}")

    def rollback(self, context: Dict[str, Any]) -> None:
        service: Service = context["service"]
        plugin = context["plugin"]
        registry: ServiceRegistry = context["service_registry"]
        
        logger.info("Rolling back process launch (terminating process)...")
        plugin.stop_service(service)
        service.pid = None
        registry.register_service(service)


class WaitForPortStep(WorkflowStep):
    @property
    def name(self) -> str:
        return "Wait for Port to Respond"

    def execute(self, context: Dict[str, Any]) -> None:
        service: Service = context["service"]
        plugin = context["plugin"]
        
        if not service.port:
            logger.info("Service does not define a TCP port. Skipping wait step.")
            return

        timeout = 5.0
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = plugin.get_status(service) if hasattr(plugin, 'get_status') else None
            if not status:
                # Fallback to get_raw_checks status check
                checks = plugin.get_raw_checks(service)
                if checks.port_responsive and checks.api_responsive:
                    status = ServiceStatus.RUNNING
            
            if status == ServiceStatus.RUNNING:
                logger.info(f"Service port {service.port} responded successfully.")
                return
            time.sleep(0.3)
            
        raise TimeoutError(f"Service failed to respond on port {service.port} within {timeout}s.")

    def rollback(self, context: Dict[str, Any]) -> None:
        pass


class DiscoveryStep(WorkflowStep):
    @property
    def name(self) -> str:
        return "Run Capabilities Discovery"

    def execute(self, context: Dict[str, Any]) -> None:
        registry: ServiceRegistry = context["service_registry"]
        cap_registry: CapabilityRegistry = context["capability_registry"]
        
        # Populate capabilities for the newly active service
        cap_registry.refresh_capabilities(registry)
        
        # Publish capabilities refreshed event if event bus is active
        event_bus = context.get("event_bus")
        service = context["service"]
        if event_bus:
            try:
                from src.backend.app.domain.event import CapabilitiesRefreshedEvent
                caps = cap_registry.get_capabilities_by_provider(service.type)
                event_bus.publish(CapabilitiesRefreshedEvent(
                    provider=service.type,
                    count=len(caps)
                ))
            except Exception as e:
                logger.error(f"Failed to publish capabilities refreshed event: {e}")

    def rollback(self, context: Dict[str, Any]) -> None:
        pass


class WorkflowEngine:
    def __init__(self, service_registry: ServiceRegistry, capability_registry: CapabilityRegistry, health_engine: HealthEngine):
        self.service_registry = service_registry
        self.capability_registry = capability_registry
        self.health_engine = health_engine
        self.event_bus = None

    def execute_start_service(self, service_id: str) -> bool:
        """Runs the start service workflow orchestration."""
        service = self.service_registry.get_service(service_id)
        if not service:
            logger.error(f"Cannot start service {service_id}: Service not found.")
            return False

        plugin = self.service_registry.get_plugin(service.type)
        if not plugin:
            logger.error(f"Cannot start service {service_id}: Plugin {service.type} not registered.")
            return False

        # Set up step sequence
        steps = [
            PreFlightCheckStep(),
            UpdateStatusStep(ServiceStatus.STARTING, ServiceStatus.ERROR),
            LaunchProcessStep(),
            WaitForPortStep(),
            DiscoveryStep(),
            UpdateStatusStep(ServiceStatus.RUNNING, ServiceStatus.ERROR)
        ]
        
        workflow = Workflow(f"Start Service: {service_id}", steps)
        context = {
            "service": service,
            "plugin": plugin,
            "service_registry": self.service_registry,
            "capability_registry": self.capability_registry,
            "health_engine": self.health_engine,
            "event_bus": self.event_bus
        }
        
        success = workflow.execute(context)
        if success and self.event_bus:
            # Publish started event
            from src.backend.app.domain.event import ServiceStartedEvent
            # reload updated state
            service = self.service_registry.get_service(service_id)
            self.event_bus.publish(ServiceStartedEvent(
                service_id=service_id,
                pid=service.pid or 0
            ))
        return success

    def execute_stop_service(self, service_id: str) -> bool:
        """Runs the stop service workflow orchestration."""
        service = self.service_registry.get_service(service_id)
        if not service:
            return False

        plugin = self.service_registry.get_plugin(service.type)
        if not plugin:
            return False

        steps = [
            UpdateStatusStep(ServiceStatus.STOPPING if hasattr(ServiceStatus, 'STOPPING') else ServiceStatus.STOPPED, ServiceStatus.RUNNING),
            UpdateStatusStep(ServiceStatus.STOPPED, ServiceStatus.RUNNING)
        ]
        
        # We manually stop the process in the first step's execute/rollback or as a custom step
        class StopProcessStep(WorkflowStep):
            @property
            def name(self) -> str:
                return "Stop Subprocess"
            def execute(self, ctx: Dict[str, Any]) -> None:
                plugin.stop_service(service)
                service.pid = None
                service.status = ServiceStatus.STOPPED
                self_reg = ctx["service_registry"]
                self_reg.register_service(service)
            def rollback(self, ctx: Dict[str, Any]) -> None:
                pass

        steps.insert(1, StopProcessStep())
        
        workflow = Workflow(f"Stop Service: {service_id}", steps)
        context = {
            "service": service,
            "plugin": plugin,
            "service_registry": self.service_registry
        }
        
        success = workflow.execute(context)
        if success and self.event_bus:
            # Publish stopped event
            from src.backend.app.domain.event import ServiceStoppedEvent
            self.event_bus.publish(ServiceStoppedEvent(service_id=service_id))
        return success
