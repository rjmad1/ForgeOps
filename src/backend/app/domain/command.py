import logging
from abc import ABC, abstractmethod
from typing import Dict, Type, Any

logger = logging.getLogger("domain.command")

class Command(ABC):
    """Base class for all intent commands."""
    pass

class StartServiceCommand(Command):
    def __init__(self, service_id: str):
        self.service_id = service_id

class StopServiceCommand(Command):
    def __init__(self, service_id: str):
        self.service_id = service_id

class RestartServiceCommand(Command):
    def __init__(self, service_id: str):
        self.service_id = service_id

class DiscoverInventoryCommand(Command):
    """Command to force refresh the machine state inventory discovery."""
    pass

class UpdateConfigCommand(Command):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value


class CommandHandler(ABC):
    @abstractmethod
    def handle(self, command: Any, kernel: Any) -> Any:
        """Processes the command logic using the Control Plane Kernel."""
        pass


class StartServiceHandler(CommandHandler):
    def handle(self, command: StartServiceCommand, kernel: Any) -> bool:
        logger.info(f"Handling StartServiceCommand for service: {command.service_id}")
        return kernel.workflow_engine.execute_start_service(command.service_id)

class StopServiceHandler(CommandHandler):
    def handle(self, command: StopServiceCommand, kernel: Any) -> bool:
        logger.info(f"Handling StopServiceCommand for service: {command.service_id}")
        return kernel.workflow_engine.execute_stop_service(command.service_id)

class RestartServiceHandler(CommandHandler):
    def handle(self, command: RestartServiceCommand, kernel: Any) -> bool:
        logger.info(f"Handling RestartServiceCommand for service: {command.service_id}")
        kernel.workflow_engine.execute_stop_service(command.service_id)
        return kernel.workflow_engine.execute_start_service(command.service_id)

class DiscoverInventoryHandler(CommandHandler):
    def handle(self, command: DiscoverInventoryCommand, kernel: Any) -> None:
        logger.info("Handling DiscoverInventoryCommand")
        kernel.inventory_engine.discover_and_populate()

class UpdateConfigHandler(CommandHandler):
    def handle(self, command: UpdateConfigCommand, kernel: Any) -> None:
        logger.info(f"Handling UpdateConfigCommand: {command.key}={command.value}")
        kernel.config_repo.set(command.key, command.value)
        # EventBus config updated
        from src.backend.app.domain.event import ConfigUpdatedEvent
        kernel.event_bus.publish(ConfigUpdatedEvent(key=command.key, value=command.value))


class CommandBus:
    def __init__(self):
        self._handlers: Dict[Type[Command], CommandHandler] = {}
        self._policy_engine = None

    def set_policy_engine(self, policy_engine: Any) -> None:
        self._policy_engine = policy_engine

    def register(self, command_type: Type[Command], handler: CommandHandler) -> None:
        self._handlers[command_type] = handler
        logger.info(f"Registered command handler for: {command_type.__name__}")

    def dispatch(self, command: Command, kernel: Any = None) -> Any:
        command_type = type(command)
        
        # Policy Evaluation
        if self._policy_engine and kernel:
            decision = self._policy_engine.evaluate(command, kernel)
            if not decision.allowed:
                logger.warning(f"Command {command_type.__name__} blocked by Policy Engine. Reason: {decision.reason}")
                raise ValueError(f"Policy violation: {decision.reason}")
                
        handler = self._handlers.get(command_type)
        if not handler:
            raise KeyError(f"No handler registered for command: {command_type.__name__}")
            
        return handler.handle(command, kernel)
