import pytest

from app.modules.weather.utils import (
    generate_recommendation,
    get_weather_condition,
)


@pytest.mark.parametrize(
    ("weather_code", "expected"),
    [
        (0, "Clear Sky"),
        (1, "Mainly Clear"),
        (2, "Partly Cloudy"),
        (3, "Overcast"),
        (45, "Fog"),
        (48, "Depositing Rime Fog"),
        (51, "Light Drizzle"),
        (53, "Moderate Drizzle"),
        (55, "Dense Drizzle"),
        (61, "Slight Rain"),
        (63, "Moderate Rain"),
        (65, "Heavy Rain"),
        (71, "Slight Snow"),
        (73, "Moderate Snow"),
        (75, "Heavy Snow"),
        (80, "Rain Showers"),
        (81, "Heavy Rain Showers"),
        (95, "Thunderstorm"),
    ],
)
def test_get_weather_condition(weather_code, expected):
    assert get_weather_condition(weather_code) == expected


@pytest.mark.parametrize(
    "weather_code",
    [-100, -1, 4, 10, 50, 82, 94, 96, 99, 1000],
)
def test_unknown_weather_code(weather_code):
    assert get_weather_condition(weather_code) == "Unknown"


def test_thunderstorm_has_highest_priority():
    result = generate_recommendation(
        weather_code=95,
        temperature=40,
        rain_probability=90,
        wind_speed=30,
    )

    assert result == (
        "Thunderstorms expected. Avoid all field work "
        "until weather improves."
    )


@pytest.mark.parametrize(
    "weather_code",
    [95, 96, 99],
)
def test_all_dangerous_weather_codes(weather_code):
    result = generate_recommendation(
        weather_code=weather_code,
        temperature=30,
        rain_probability=20,
        wind_speed=10,
    )

    assert "Thunderstorms expected" in result
    assert "Avoid all field work" in result


def test_heavy_rain_recommendation():
    result = generate_recommendation(
        weather_code=61,
        temperature=30,
        rain_probability=70,
        wind_speed=10,
    )

    assert result == (
        "Heavy rain is expected today. "
        "Avoid irrigation and monitor drainage."
    )


@pytest.mark.parametrize(
    "rain_probability",
    [70, 75, 90, 100],
)
def test_heavy_rain_threshold(rain_probability):
    result = generate_recommendation(
        weather_code=0,
        temperature=25,
        rain_probability=rain_probability,
        wind_speed=10,
    )

    assert "Heavy rain is expected" in result


@pytest.mark.parametrize(
    "rain_probability",
    [None, 0, 1, 50, 69],
)
def test_heavy_rain_not_triggered_below_threshold(rain_probability):
    result = generate_recommendation(
        weather_code=0,
        temperature=25,
        rain_probability=rain_probability,
        wind_speed=10,
    )

    assert "Heavy rain is expected" not in result


def test_strong_wind_recommendation():
    result = generate_recommendation(
        weather_code=0,
        temperature=25,
        rain_probability=20,
        wind_speed=25,
    )

    assert result == (
        "Strong winds detected. "
        "Avoid pesticide spraying."
    )


@pytest.mark.parametrize(
    "wind_speed",
    [25, 30, 50, 100],
)
def test_strong_wind_threshold(wind_speed):
    result = generate_recommendation(
        weather_code=0,
        temperature=25,
        rain_probability=10,
        wind_speed=wind_speed,
    )

    assert "Strong winds detected" in result


def test_strong_wind_not_triggered_below_threshold():
    result = generate_recommendation(
        weather_code=0,
        temperature=25,
        rain_probability=10,
        wind_speed=24.9,
    )

    assert "Strong winds detected" not in result


def test_high_temperature_recommendation():
    result = generate_recommendation(
        weather_code=0,
        temperature=35,
        rain_probability=10,
        wind_speed=10,
    )

    assert result == (
        "High temperature today. "
        "Irrigate early morning or evening."
    )


@pytest.mark.parametrize(
    "temperature",
    [35, 36, 40, 50],
)
def test_high_temperature_threshold(temperature):
    result = generate_recommendation(
        weather_code=0,
        temperature=temperature,
        rain_probability=10,
        wind_speed=10,
    )

    assert "High temperature today" in result


def test_high_temperature_not_triggered_below_threshold():
    result = generate_recommendation(
        weather_code=0,
        temperature=34.9,
        rain_probability=10,
        wind_speed=10,
    )

    assert "High temperature today" not in result


def test_normal_weather_recommendation():
    result = generate_recommendation(
        weather_code=0,
        temperature=25,
        rain_probability=10,
        wind_speed=10,
    )

    assert result == (
        "Weather conditions are favorable "
        "for normal farming activities."
    )


def test_none_rain_probability_does_not_fail():
    result = generate_recommendation(
        weather_code=0,
        temperature=25,
        rain_probability=None,
        wind_speed=10,
    )

    assert "favorable" in result