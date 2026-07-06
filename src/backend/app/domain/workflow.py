import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

logger = logging.getLogger("workflow")

class WorkflowStep(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the step."""
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> None:
        """Executes the step. Must raise an exception on failure."""
        pass

    @abstractmethod
    def rollback(self, context: Dict[str, Any]) -> None:
        """Undoes the step if execution of subsequent steps in the workflow fails."""
        pass


class Workflow:
    def __init__(self, name: str, steps: List[WorkflowStep]):
        self.name = name
        self.steps = steps
        self.completed_steps: List[WorkflowStep] = []

    def execute(self, context: Dict[str, Any]) -> bool:
        """Executes workflow steps. Triggers rollbacks in reverse order on failure."""
        logger.info(f"Starting workflow '{self.name}'...")
        self.completed_steps = []
        
        for step in self.steps:
            logger.info(f"Executing step '{step.name}'...")
            try:
                step.execute(context)
                self.completed_steps.append(step)
            except Exception as e:
                logger.error(f"Step '{step.name}' failed: {e}. Initiating rollback...")
                self._rollback(context)
                return False
                
        logger.info(f"Workflow '{self.name}' completed successfully.")
        return True

    def _rollback(self, context: Dict[str, Any]) -> None:
        """Rolls back all completed steps in reverse execution order."""
        for step in reversed(self.completed_steps):
            logger.info(f"Rolling back step '{step.name}'...")
            try:
                step.rollback(context)
            except Exception as e:
                logger.error(f"Rollback step '{step.name}' failed: {e}")
