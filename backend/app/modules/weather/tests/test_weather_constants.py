import pytest

from app.modules.weather.constants import WEATHER_CODES


def test_weather_codes_is_dict():
    assert isinstance(WEATHER_CODES, dict)


def test_weather_codes_are_strings():
    assert all(isinstance(code, int) for code in WEATHER_CODES)
    assert all(isinstance(description, str) for description in WEATHER_CODES.values())


def test_weather_codes_contains_expected_codes():
    expected_codes = {
        0,
        1,
        2,
        3,
        45,
        48,
        51,
        53,
        55,
        61,
        63,
        65,
        71,
        73,
        75,
        80,
        81,
        95,
    }

    assert set(WEATHER_CODES.keys()) == expected_codes


@pytest.mark.parametrize(
    ("code", "expected"),
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
def test_weather_code_description(code, expected):
    assert WEATHER_CODES[code] == expected