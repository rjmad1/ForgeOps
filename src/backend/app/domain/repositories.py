from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .models import Service, Capability

class ServiceRepository(ABC):
    @abstractmethod
    def save(self, service: Service) -> None:
        """Saves or updates a service entity."""
        pass

    @abstractmethod
    def get_by_id(self, service_id: str) -> Optional[Service]:
        """Retrieves a service by its ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Service]:
        """Retrieves all services."""
        pass

    @abstractmethod
    def delete(self, service_id: str) -> None:
        """Deletes a service by its ID."""
        pass

class CapabilityRepository(ABC):
    @abstractmethod
    def save(self, capability: Capability) -> None:
        """Saves or updates a capability entity."""
        pass

    @abstractmethod
    def get_by_id(self, capability_id: str) -> Optional[Capability]:
        """Retrieves a capability by its ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Capability]:
        """Retrieves all capabilities."""
        pass

    @abstractmethod
    def get_by_provider(self, provider: str) -> List[Capability]:
        """Retrieves all capabilities registered for a given provider."""
        pass

    @abstractmethod
    def delete(self, capability_id: str) -> None:
        """Deletes a capability by its ID."""
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """Clears all capability records from the repository."""
        pass

    @abstractmethod
    def clear_by_provider(self, provider: str) -> None:
        """Clears all capability records for a specific provider."""
        pass

class SystemConfigRepository(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Retrieves config value by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """Sets/updates key to value."""
        pass


class SystemInventoryRepository(ABC):
    @abstractmethod
    def save(self, key: str, category: str, value: str) -> None:
        """Saves or updates system inventory value."""
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves an inventory value by key."""
        pass

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieves all inventory items."""
        pass


class OperationalHistoryRepository(ABC):
    @abstractmethod
    def log(self, event_type: str, severity: str, message: str, service_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Records an operational event in history."""
        pass

    @abstractmethod
    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves recent operational events."""
        pass

