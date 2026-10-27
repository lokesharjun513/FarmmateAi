from types import SimpleNamespace

from app.modules.onboarding.service import (
    get_next_step,
)


# ============================================================
# HELPERS
# ============================================================


def make_farmer(
    profile_completion: int,
):

    return SimpleNamespace(
        profile_completion=profile_completion,
    )


# ============================================================
# NO FARMER
# ============================================================


def test_get_next_step_without_farmer():

    result = get_next_step(None)

    assert result == {
        "step": "language",
        "title": "Welcome to FarmMate AI",
        "message": "Which language do you prefer?",
        "progress": 0,
        "completed": False,
    }


# ============================================================
# PROFILE STARTED
# ============================================================


def test_get_next_step_profile_completion_zero():

    farmer = make_farmer(
        profile_completion=0,
    )

    result = get_next_step(farmer)

    assert result == {
        "step": "language",
        "title": "Welcome to FarmMate AI",
        "message": "Which language do you prefer?",
        "progress": 0,
        "completed": False,
    }


def test_get_next_step_profile_completion_below_20():

    farmer = make_farmer(
        profile_completion=10,
    )

    result = get_next_step(farmer)

    assert result == {
        "step": "language",
        "title": "Welcome to FarmMate AI",
        "message": "Which language do you prefer?",
        "progress": 10,
        "completed": False,
    }


def test_get_next_step_profile_completion_19():

    farmer = make_farmer(
        profile_completion=19,
    )

    result = get_next_step(farmer)

    assert result["step"] == "language"
    assert result["progress"] == 19
    assert result["completed"] is False


# ============================================================
# FARM DETAILS
# ============================================================


def test_get_next_step_profile_completion_20():

    farmer = make_farmer(
        profile_completion=20,
    )

    result = get_next_step(farmer)

    assert result == {
        "step": "farm",
        "title": "Let's add your first farm",
        "message": "Tell me about your farm.",
        "progress": 20,
        "completed": False,
    }


def test_get_next_step_profile_completion_50():

    farmer = make_farmer(
        profile_completion=50,
    )

    result = get_next_step(farmer)

    assert result["step"] == "farm"
    assert result["title"] == (
        "Let's add your first farm"
    )
    assert result["message"] == (
        "Tell me about your farm."
    )
    assert result["progress"] == 50
    assert result["completed"] is False


def test_get_next_step_profile_completion_99():

    farmer = make_farmer(
        profile_completion=99,
    )

    result = get_next_step(farmer)

    assert result["step"] == "farm"
    assert result["progress"] == 99
    assert result["completed"] is False


# ============================================================
# COMPLETED
# ============================================================


def test_get_next_step_profile_completion_100():

    farmer = make_farmer(
        profile_completion=100,
    )

    result = get_next_step(farmer)

    assert result == {
        "step": "completed",
        "title": "You're all set!",
        "message": "Let's start farming.",
        "progress": 100,
        "completed": True,
    }


def test_get_next_step_profile_completion_above_100():

    farmer = make_farmer(
        profile_completion=101,
    )

    result = get_next_step(farmer)

    assert result == {
        "step": "completed",
        "title": "You're all set!",
        "message": "Let's start farming.",
        "progress": 100,
        "completed": True,
    }


# ============================================================
# RETURN TYPE
# ============================================================


def test_get_next_step_returns_dict():

    farmer = make_farmer(
        profile_completion=50,
    )

    result = get_next_step(farmer)

    assert isinstance(
        result,
        dict,
    )


# ============================================================
# RESULT STRUCTURE
# ============================================================


def test_get_next_step_contains_all_required_fields():

    farmer = make_farmer(
        profile_completion=50,
    )

    result = get_next_step(farmer)

    assert set(result.keys()) == {
        "step",
        "title",
        "message",
        "progress",
        "completed",
    }