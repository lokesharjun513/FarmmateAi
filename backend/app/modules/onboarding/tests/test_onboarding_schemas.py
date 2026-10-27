from pydantic import ValidationError
import pytest

from app.modules.onboarding.schemas import (
    OnboardingStep,
)


# ============================================================
# VALID
# ============================================================


def test_onboarding_step_valid():

    step = OnboardingStep(
        step="language",
        title="Welcome to FarmMate AI",
        message="Which language do you prefer?",
        progress=0,
        completed=False,
    )

    assert step.step == "language"
    assert step.title == "Welcome to FarmMate AI"
    assert step.message == "Which language do you prefer?"
    assert step.progress == 0
    assert step.completed is False


def test_onboarding_step_completed():

    step = OnboardingStep(
        step="completed",
        title="You're all set!",
        message="Let's start farming.",
        progress=100,
        completed=True,
    )

    assert step.step == "completed"
    assert step.progress == 100
    assert step.completed is True


# ============================================================
# REQUIRED FIELDS
# ============================================================


@pytest.mark.parametrize(
    "field",
    [
        "step",
        "title",
        "message",
        "progress",
        "completed",
    ],
)
def test_onboarding_step_requires_field(field):

    data = {
        "step": "language",
        "title": "Welcome",
        "message": "Which language do you prefer?",
        "progress": 0,
        "completed": False,
    }

    del data[field]

    with pytest.raises(ValidationError):

        OnboardingStep(**data)


# ============================================================
# TYPES
# ============================================================


def test_onboarding_step_progress_must_be_integer():

    with pytest.raises(ValidationError):

        OnboardingStep(
            step="language",
            title="Welcome",
            message="Which language do you prefer?",
            progress="invalid",
            completed=False,
        )


def test_onboarding_step_completed_must_be_boolean():

    # Pydantic accepts some coercible values, so use a value
    # that cannot be interpreted as a boolean.
    with pytest.raises(ValidationError):

        OnboardingStep(
            step="language",
            title="Welcome",
            message="Which language do you prefer?",
            progress=0,
            completed="not-a-boolean",
        )


# ============================================================
# EXTRA FIELDS
# ============================================================


def test_onboarding_step_ignores_extra_fields():

    step = OnboardingStep(
        step="language",
        title="Welcome",
        message="Which language do you prefer?",
        progress=0,
        completed=False,
        extra_field="ignored",
    )

    assert step.step == "language"

    assert not hasattr(
        step,
        "extra_field",
    )