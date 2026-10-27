from app.modules.farmer.models import Farmer

from app.modules.workflow.handlers.base import (
    BaseWorkflowHandler,
)
from app.modules.workflow.schemas import (
    WorkflowContext,
    WorkflowResult,
)


class GreetingHandler(BaseWorkflowHandler):
    """
    Handles greeting messages.

    Examples:
        Hi
        Hello
        Hey
        Good Morning
    """

    async def handle(
        self,
        *,
        farmer: Farmer,
        context: WorkflowContext,
        message: str,
    ) -> WorkflowResult:

        name = (
            farmer.user.full_name
            if farmer.user
            else "Farmer"
        )

        response = (
            f"Hello {name}! 👋\n\n"
            "I'm FarmMate AI.\n"
            "How can I help you today?\n\n"
            "You can ask me to:\n"
            "• Start a new crop\n"
            "• View today's tasks\n"
            "• Check today's weather\n"
            "• Get farming advice\n"
            "• Track your crop progress"
        )

        return WorkflowResult(
            handled=True,
            response=response,
            next_state=context.state,
            pending_action=context.pending_action,
            metadata=context.metadata,
        )