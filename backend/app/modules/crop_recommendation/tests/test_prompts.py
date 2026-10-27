from app.modules.crop_recommendation.prompts import (
    crop_recommendation_system_prompt,
    crop_recommendation_user_prompt,
)


def test_system_prompt_contains_farmmate_identity():

    prompt = crop_recommendation_system_prompt()

    assert "FarmMate AI" in prompt


def test_system_prompt_requires_exactly_three_crops():

    prompt = crop_recommendation_system_prompt()

    assert "exactly THREE crops" in prompt


def test_system_prompt_requires_confidence():

    prompt = crop_recommendation_system_prompt()

    assert "confidence score" in prompt


def test_system_prompt_requires_json():

    prompt = crop_recommendation_system_prompt()

    assert "ONLY valid JSON" in prompt


def test_system_prompt_disallows_markdown():

    prompt = crop_recommendation_system_prompt()

    assert "Do NOT use markdown" in prompt
    assert "Do NOT use code fences" in prompt


def test_system_prompt_handles_unknown_values():

    prompt = crop_recommendation_system_prompt()

    assert "Unknown" in prompt


def test_user_prompt_contains_location():

    prompt = crop_recommendation_user_prompt(
        state="Andhra Pradesh",
        district="Nellore",
        village="Test Village",
        season="KHARIF",
        land_area=1.0,
        land_unit="Acres",
        soil_type=None,
        water_source=None,
        water_availability=None,
        irrigation_method=None,
        temperature=30.0,
        humidity=70.0,
        rain_probability=60.0,
        weather_condition="Cloudy",
    )

    assert "Andhra Pradesh" in prompt
    assert "Nellore" in prompt
    assert "Test Village" in prompt


def test_user_prompt_contains_farm_conditions():

    prompt = crop_recommendation_user_prompt(
        state="Andhra Pradesh",
        district="Nellore",
        village="Village",
        season="KHARIF",
        land_area=2.5,
        land_unit="Acres",
        soil_type="Clay",
        water_source="Borewell",
        water_availability="High",
        irrigation_method="Drip",
        temperature=31.5,
        humidity=72.0,
        rain_probability=45.0,
        weather_condition="Partly Cloudy",
    )

    assert "2.5 Acres" in prompt
    assert "Clay" in prompt
    assert "Borewell" in prompt
    assert "High" in prompt
    assert "Drip" in prompt


def test_user_prompt_contains_weather():

    prompt = crop_recommendation_user_prompt(
        state="Andhra Pradesh",
        district="Nellore",
        village="Village",
        season="KHARIF",
        land_area=1.0,
        land_unit="Acres",
        soil_type=None,
        water_source=None,
        water_availability=None,
        irrigation_method=None,
        temperature=32.0,
        humidity=75.0,
        rain_probability=80.0,
        weather_condition="Rain",
    )

    assert "32.0" in prompt
    assert "75.0" in prompt
    assert "80.0" in prompt
    assert "Rain" in prompt


def test_user_prompt_uses_unknown_for_missing_conditions():

    prompt = crop_recommendation_user_prompt(
        state="Andhra Pradesh",
        district="Nellore",
        village="Village",
        season="KHARIF",
        land_area=1.0,
        land_unit="Acres",
        soil_type=None,
        water_source=None,
        water_availability=None,
        irrigation_method=None,
        temperature=30.0,
        humidity=70.0,
        rain_probability=20.0,
        weather_condition="Clear",
    )

    assert prompt.count("Unknown") >= 4