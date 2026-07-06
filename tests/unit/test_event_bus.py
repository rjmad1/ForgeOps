import pytest
from dataclasses import dataclass
from src.backend.app.domain.event import EventBus, Event, ServiceStartedEvent

@dataclass
class MockEvent(Event):
    value: str = "test"

def test_event_bus_delivery():
    bus = EventBus()
    received = []

    def handler(event: MockEvent):
        received.append(event.value)

    bus.subscribe(MockEvent, handler)
    bus.publish(MockEvent(value="hello"))

    assert len(received) == 1
    assert received[0] == "hello"

def test_event_bus_handler_isolation():
    bus = EventBus()
    received = []

    def failing_handler(event: MockEvent):
        raise ValueError("broken handler")

    def normal_handler(event: MockEvent):
        received.append(event.value)

    # Register failing handler first
    bus.subscribe(MockEvent, failing_handler)
    bus.subscribe(MockEvent, normal_handler)

    # Publish should not raise an exception, and should reach the normal handler
    bus.publish(MockEvent(value="safe"))

    assert len(received) == 1
    assert received[0] == "safe"
