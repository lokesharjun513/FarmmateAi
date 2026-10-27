from app.modules.advisor.prompts import (
    advisor_system_prompt,
    advisor_user_prompt,
)


# ============================================================
# SYSTEM PROMPT
# ============================================================


def test_advisor_system_prompt_is_not_empty():

    prompt = advisor_system_prompt()

    assert prompt
    assert isinstance(prompt, str)


def test_advisor_system_prompt_contains_role():

    prompt = advisor_system_prompt()

    assert "FarmMate AI" in prompt
    assert "senior agricultural expert" in prompt


def test_advisor_system_prompt_requires_json():

    prompt = advisor_system_prompt()

    assert "ONLY valid JSON" in prompt
    assert "Never use Markdown" in prompt
    assert "Never return ```json" in prompt


def test_advisor_system_prompt_contains_priority_rules():

    prompt = advisor_system_prompt()

    assert "LOW" in prompt
    assert "MEDIUM" in prompt
    assert "HIGH" in prompt


def test_advisor_system_prompt_contains_safety_rules():

    prompt = advisor_system_prompt()

    assert "Never invent diseases or pests." in prompt
    assert "Base every recommendation on the provided farm context." in prompt


# ============================================================
# USER PROMPT
# ============================================================


def create_prompt():

    return advisor_user_prompt(
        crop_name="Rice",
        crop_variety="BPT 5204",
        crop_age_days=45,
        soil_type="Clay Loam",
        location="Kavali, Nellore",
        weather="Clear Sky",
        temperature=32.5,
        humidity=70,
        rain_probability=20,
        today_activities=[
            "Irrigate field",
            "Inspect crop",
        ],
    )


def test_user_prompt_contains_crop_information():

    prompt = create_prompt()

    assert "Rice" in prompt
    assert "BPT 5204" in prompt
    assert "45 days" in prompt
    assert "Clay Loam" in prompt


def test_user_prompt_contains_location():

    prompt = create_prompt()

    assert "Kavali, Nellore" in prompt


def test_user_prompt_contains_weather():

    prompt = create_prompt()

    assert "Clear Sky" in prompt
    assert "32.5" in prompt
    assert "70%" in prompt
    assert "20%" in prompt


def test_user_prompt_contains_activities():

    prompt = create_prompt()

    assert "Irrigate field" in prompt
    assert "Inspect crop" in prompt


def test_user_prompt_handles_empty_activities():

    prompt = advisor_user_prompt(
        crop_name="Rice",
        crop_variety=None,
        crop_age_days=30,
        soil_type=None,
        location="Nellore",
        weather="Cloudy",
        temperature=30.0,
        humidity=80,
        rain_probability=60,
        today_activities=[],
    )

    assert "- No planned activities" in prompt


def test_user_prompt_handles_missing_variety():

    prompt = advisor_user_prompt(
        crop_name="Rice",
        crop_variety=None,
        crop_age_days=30,
        soil_type="Clay",
        location="Nellore",
        weather="Clear Sky",
        temperature=30.0,
        humidity=60,
        rain_probability=10,
        today_activities=[],
    )

    assert "Variety:" in prompt
    assert "Unknown" in prompt


def test_user_prompt_handles_missing_soil():

    prompt = advisor_user_prompt(
        crop_name="Rice",
        crop_variety="BPT 5204",
        crop_age_days=30,
        soil_type=None,
        location="Nellore",
        weather="Clear Sky",
        temperature=30.0,
        humidity=60,
        rain_probability=10,
        today_activities=[],
    )

    assert "Soil:" in prompt
    assert "Unknown" in prompt


def test_user_prompt_requires_json_structure():

    prompt = create_prompt()

    assert '"summary"' in prompt
    assert '"warnings"' in prompt
    assert '"recommendations"' in prompt
    assert '"priority"' in prompt


def test_user_prompt_contains_advisory_questions():

    prompt = create_prompt()

    assert "Should irrigation be done?" in prompt
    assert "Should fertilizer be applied?" in prompt
    assert "Should pesticide spraying be avoided?" in prompt
    assert "Is rain likely to affect today's work?" in prompt
    assert "What should the farmer do today?" in prompt