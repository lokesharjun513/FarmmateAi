from typing import Any

from pydantic import BaseModel, Field

from app.modules.workflow.enums import (
    PendingAction,
    WorkflowIntent,
    WorkflowState,
)


class WorkflowRequest(BaseModel):
    """
    Incoming farmer message.
    """

    message: str = Field(
        min_length=1,
        max_length=2000,
    )


class WorkflowContext(BaseModel):
    """
    Runtime workflow information.

    This is built before executing
    a workflow handler.
    """

    farmer_id: str

    farm_id: str | None = None

    crop_season_id: str | None = None

    intent: WorkflowIntent

    state: WorkflowState = WorkflowState.IDLE

    pending_action: PendingAction = PendingAction.NONE

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class WorkflowResult(BaseModel):
    """
    Output returned by every workflow handler.
    """

    handled: bool = False

    response: str | None = None

    next_state: WorkflowState = WorkflowState.IDLE

    pending_action: PendingAction = PendingAction.NONE

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class WorkflowResponse(BaseModel):
    """
    Final response sent back
    to ChatService.
    """

    response: str

    context: WorkflowContext