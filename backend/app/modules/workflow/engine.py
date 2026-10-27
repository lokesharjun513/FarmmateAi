from app.modules.farmer.models import Farmer

from app.modules.workflow.detector import IntentDetector
from app.modules.workflow.registry import WorkflowRegistry

from app.modules.workflow.schemas import (
    WorkflowContext,
    WorkflowResult,
)

from app.modules.workflow.enums import (
    PendingAction,
    WorkflowState,
)


class WorkflowEngine:
    """
    Central Workflow Engine.

    Responsibilities:

    1. Detect farmer intent
    2. Build workflow context
    3. Find handler
    4. Execute handler
    5. Return workflow result
    """

    def __init__(self):

        self.detector = IntentDetector()

        self.registry = WorkflowRegistry()

    async def process(
        self,
        *,
        farmer: Farmer,
        message: str,
    ) -> WorkflowResult:

        # ----------------------------
        # Detect Intent
        # ----------------------------

        intent = self.detector.detect(
            message,
        )

        # ----------------------------
        # Build Context
        # ----------------------------

        context = WorkflowContext(
            farmer_id=farmer.id,

            intent=intent,

            state=WorkflowState.IDLE,

            pending_action=PendingAction.NONE,
        )

        # ----------------------------
        # Find Handler
        # ----------------------------

        handler = self.registry.get_handler(
            intent,
        )

        # ----------------------------
        # No Handler
        # ----------------------------

        if handler is None:

            return WorkflowResult(
                handled=False,
            )

        # ----------------------------
        # Execute Handler
        # ----------------------------

        return await handler.handle(
            farmer=farmer,
            context=context,
            message=message,
        )