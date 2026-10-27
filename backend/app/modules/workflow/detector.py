from app.modules.workflow.enums import WorkflowIntent


class IntentDetector:
    """
    Detects the farmer's intent from
    the incoming message.

    Uses lightweight rule matching.

    The AI Workflow Engine can later
    replace or enhance this detector.
    """

    def detect(
        self,
        message: str,
    ) -> WorkflowIntent:

        text = message.lower().strip()

        # -----------------------------
        # Greetings
        # -----------------------------

        if any(
            word in text
            for word in (
                "hi",
                "hello",
                "hey",
                "good morning",
                "good evening",
            )
        ):
            return WorkflowIntent.GREETING

        # -----------------------------
        # Start Crop
        # -----------------------------

        if any(
            phrase in text
            for phrase in (
                "start crop",
                "start farming",
                "grow crop",
                "cultivate",
                "plant crop",
                "new crop",
            )
        ):
            return WorkflowIntent.START_CROP

        # -----------------------------
        # Weather
        # -----------------------------

        if any(
            word in text
            for word in (
                "weather",
                "rain",
                "temperature",
                "humidity",
                "wind",
            )
        ):
            return WorkflowIntent.ASK_WEATHER

        # -----------------------------
        # Today Tasks
        # -----------------------------

        if any(
            phrase in text
            for phrase in (
                "today task",
                "today work",
                "what should i do",
                "today activities",
            )
        ):
            return WorkflowIntent.TODAY_TASKS

        # -----------------------------
        # Complete Task
        # -----------------------------

        if any(
            phrase in text
            for phrase in (
                "completed",
                "done",
                "finished",
                "completed irrigation",
                "task completed",
            )
        ):
            return WorkflowIntent.COMPLETE_TASK

        # -----------------------------
        # Crop Plan
        # -----------------------------

        if any(
            phrase in text
            for phrase in (
                "crop plan",
                "show plan",
                "farming plan",
            )
        ):
            return WorkflowIntent.SHOW_PLAN

        # -----------------------------
        # Progress
        # -----------------------------

        if any(
            phrase in text
            for phrase in (
                "progress",
                "status",
                "how is my crop",
            )
        ):
            return WorkflowIntent.SHOW_PROGRESS

        # -----------------------------
        # Advice
        # -----------------------------

        if any(
            phrase in text
            for phrase in (
                "suggest",
                "recommend",
                "advice",
                "help me",
            )
        ):
            return WorkflowIntent.ASK_ADVICE

        return WorkflowIntent.GENERAL_CHAT