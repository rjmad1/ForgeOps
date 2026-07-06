from dataclasses import dataclass, field
from typing import Callable, Dict, List, Type, Any
from datetime import datetime

@dataclass
class Event:
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ServiceStartedEvent(Event):
    service_id: str = ""
    pid: int = 0

@dataclass
class ServiceStoppedEvent(Event):
    service_id: str = ""

@dataclass
class HealthChangedEvent(Event):
    service_id: str = ""
    old_status: str = ""
    new_status: str = ""

@dataclass
class ConfigUpdatedEvent(Event):
    key: str = ""
    value: str = ""

@dataclass
class CapabilitiesRefreshedEvent(Event):
    provider: str = ""
    count: int = 0

class EventBus:
    def __init__(self):
        self._subscribers: Dict[Type[Event], List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: Type[Event], callback: Callable[[Any], None]) -> None:
        """Registers a subscriber callback for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event: Event) -> None:
        """Publishes an event to all registered subscribers."""
        event_type = type(event)
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception:
                    # Ignore or log exceptions in subscriber callbacks to prevent cascading failure
                    pass
