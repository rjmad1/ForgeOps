import logging
from typing import Dict, List, Optional
from .models import Service, Capability, ServiceStatus, ServiceMetrics
from .repositories import ServiceRepository, CapabilityRepository
from .plugin import RuntimePlugin

logger = logging.getLogger("registry")

class ServiceRegistry:
    def __init__(self, service_repository: ServiceRepository):
        self.repository = service_repository
        self._plugins: Dict[str, RuntimePlugin] = {}

    def register_plugin(self, plugin: RuntimePlugin) -> None:
        """Registers a runtime plugin."""
        identifier = plugin.get_identifier()
        self._plugins[identifier] = plugin
        logger.info(f"Registered runtime plugin: {identifier}")

    def get_plugin(self, identifier: str) -> Optional[RuntimePlugin]:
        """Gets a registered plugin by identifier."""
        return self._plugins.get(identifier)

    def list_plugins(self) -> List[RuntimePlugin]:
        """Lists all registered plugins."""
        return list(self._plugins.values())

    def register_service(self, service: Service) -> None:
        """Persists/updates a service definition."""
        self.repository.save(service)
        logger.info(f"Registered service in database: {service.id} ({service.name})")

    def get_service(self, service_id: str) -> Optional[Service]:
        """Gets service from database."""
        return self.repository.get_by_id(service_id)

    def list_services(self) -> List[Service]:
        """Lists all services from database."""
        return self.repository.get_all()

    def start_service(self, service_id: str) -> bool:
        """Starts a service by delegating to its plugin."""
        service = self.get_service(service_id)
        if not service:
            logger.error(f"Cannot start service {service_id}: Service not found.")
            return False

        plugin = self.get_plugin(service.type)
        if not plugin:
            logger.error(f"Cannot start service {service_id}: Plugin {service.type} not registered.")
            return False

        try:
            service.status = ServiceStatus.STARTING
            self.repository.save(service)

            pid = plugin.start_service(service)
            if pid > 0:
                service.pid = pid
                service.status = ServiceStatus.RUNNING
                self.repository.save(service)
                logger.info(f"Successfully started service {service_id} with PID {pid}.")
                return True
            else:
                service.status = ServiceStatus.ERROR
                self.repository.save(service)
                logger.error(f"Plugin failed to launch process for service {service_id}.")
                return False
        except Exception as e:
            service.status = ServiceStatus.ERROR
            self.repository.save(service)
            logger.error(f"Exception starting service {service_id}: {e}", exc_info=True)
            return False

    def stop_service(self, service_id: str) -> bool:
        """Stops a service by delegating to its plugin."""
        service = self.get_service(service_id)
        if not service:
            logger.error(f"Cannot stop service {service_id}: Service not found.")
            return False

        plugin = self.get_plugin(service.type)
        if not plugin:
            logger.error(f"Cannot stop service {service_id}: Plugin {service.type} not registered.")
            return False

        try:
            success = plugin.stop_service(service)
            if success:
                service.pid = None
                service.status = ServiceStatus.STOPPED
                self.repository.save(service)
                logger.info(f"Successfully stopped service {service_id}.")
                return True
            else:
                logger.error(f"Plugin failed to stop service {service_id}.")
                return False
        except Exception as e:
            logger.error(f"Exception stopping service {service_id}: {e}", exc_info=True)
            return False

    def update_service_status(self, service_id: str) -> ServiceStatus:
        """Returns the current database status of the service (decoupling active checks to HealthEngine)."""
        service = self.get_service(service_id)
        if not service:
            return ServiceStatus.ERROR
        return service.status


class CapabilityRegistry:
    def __init__(self, capability_repository: CapabilityRepository):
        self.repository = capability_repository

    def register_capability(self, capability: Capability) -> None:
        """Saves capability to the repository."""
        self.repository.save(capability)

    def list_capabilities(self) -> List[Capability]:
        """Lists all capabilities."""
        return self.repository.get_all()

    def get_capabilities_by_provider(self, provider: str) -> List[Capability]:
        """Lists capabilities by provider."""
        return self.repository.get_by_provider(provider)

    def refresh_capabilities(self, service_registry: ServiceRegistry) -> None:
        """Triggers capability discovery on all active plugins and registers them."""
        # Only query plugins that have a corresponding active service registered in the database
        active_service_types = {s.type for s in service_registry.list_services()}
        
        for plugin in service_registry.list_plugins():
            provider = plugin.get_identifier()
            if provider not in active_service_types:
                # Skip discovery if the service is not active/available on this host
                continue
            try:
                # Query capabilities from plugin
                capabilities = plugin.discover_capabilities()
                
                # Clear existing capabilities for this provider first
                self.repository.clear_by_provider(provider)
                
                # Save new capabilities
                for cap in capabilities:
                    self.register_capability(cap)
                logger.info(f"Refreshed {len(capabilities)} capabilities for provider: {provider}")
            except Exception as e:
                logger.error(f"Failed to refresh capabilities for {provider}: {e}", exc_info=True)
