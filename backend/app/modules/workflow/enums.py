from enum import Enum


class WorkflowIntent(str, Enum):
    """
    Supported workflow intents.

    These intents are detected from the farmer's message
    and determine which business workflow should execute.
    """

    GREETING = "GREETING"

    START_CROP = "START_CROP"

    SELECT_FARM = "SELECT_FARM"

    SELECT_CROP = "SELECT_CROP"

    TODAY_TASKS = "TODAY_TASKS"

    COMPLETE_TASK = "COMPLETE_TASK"

    POSTPONE_TASK = "POSTPONE_TASK"

    UPDATE_ACTIVITY = "UPDATE_ACTIVITY"

    SHOW_PLAN = "SHOW_PLAN"

    SHOW_PROGRESS = "SHOW_PROGRESS"

    ASK_WEATHER = "ASK_WEATHER"

    ASK_ADVICE = "ASK_ADVICE"

    GENERAL_CHAT = "GENERAL_CHAT"

    UNKNOWN = "UNKNOWN"


class WorkflowState(str, Enum):
    """
    Current conversation state.

    Used by the AI State Manager to understand
    what the assistant is waiting for.
    """

    IDLE = "IDLE"

    WAITING_FOR_FARM = "WAITING_FOR_FARM"

    WAITING_FOR_CROP = "WAITING_FOR_CROP"

    WAITING_FOR_SOWING_DATE = "WAITING_FOR_SOWING_DATE"

    WAITING_FOR_PLAN_CONFIRMATION = "WAITING_FOR_PLAN_CONFIRMATION"

    ACTIVE = "ACTIVE"


class PendingAction(str, Enum):
    """
    Pending action awaiting user confirmation.
    """

    NONE = "NONE"

    START_CROP = "START_CROP"

    COMPLETE_ACTIVITY = "COMPLETE_ACTIVITY"

    POSTPONE_ACTIVITY = "POSTPONE_ACTIVITY"

    GENERATE_PLAN = "GENERATE_PLAN"

    UPDATE_PLAN = "UPDATE_PLAN"