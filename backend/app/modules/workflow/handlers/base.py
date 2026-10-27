from abc import ABC, abstractmethod

from app.modules.farmer.models import Farmer

from app.modules.workflow.schemas import (
    WorkflowContext,
    WorkflowResult,
)


class BaseWorkflowHandler(ABC):
    """
    Base class for all workflow handlers.

    Every workflow handler must implement
    the handle() method.
    """

    @abstractmethod
    async def handle(
        self,
        *,
        farmer: Farmer,
        context: WorkflowContext,
        message: str,
    ) -> WorkflowResult:
        """
        Execute workflow.

        Returns:
            WorkflowResult
        """
        raise NotImplementedError