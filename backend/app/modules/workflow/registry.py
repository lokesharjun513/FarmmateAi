from app.modules.workflow.enums import WorkflowIntent

from app.modules.workflow.handlers.base import (
    BaseWorkflowHandler,
)

from app.modules.workflow.handlers.greeting import (
    GreetingHandler,
)


class WorkflowRegistry:
    """
    Maps workflow intents
    to their corresponding handlers.
    """

    def __init__(self):

        self._handlers: dict[
            WorkflowIntent,
            BaseWorkflowHandler,
        ] = {

            WorkflowIntent.GREETING:
                GreetingHandler(),

        }

    def register(
        self,
        intent: WorkflowIntent,
        handler: BaseWorkflowHandler,
    ) -> None:

        self._handlers[intent] = handler

    def get_handler(
        self,
        intent: WorkflowIntent,
    ) -> BaseWorkflowHandler | None:

        return self._handlers.get(intent)