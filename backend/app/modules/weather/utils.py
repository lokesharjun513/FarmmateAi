from app.modules.weather.constants import WEATHER_CODES


def get_weather_condition(
    weather_code: int,
) -> str:
    return WEATHER_CODES.get(
        weather_code,
        "Unknown",
    )


def generate_recommendation(
    *,
    weather_code: int,
    temperature: float,
    rain_probability: int | None,
    wind_speed: float,
) -> str:

    #
    # Dangerous weather first
    #

    if weather_code in (95, 96, 99):
        return (
            "Thunderstorms expected. Avoid all field work "
            "until weather improves."
        )

    #
    # Heavy rain
    #

    if rain_probability is not None and rain_probability >= 70:
        return (
            "Heavy rain is expected today. "
            "Avoid irrigation and monitor drainage."
        )

    #
    # Strong wind
    #

    if wind_speed >= 25:
        return (
            "Strong winds detected. "
            "Avoid pesticide spraying."
        )

    #
    # High temperature
    #

    if temperature >= 35:
        return (
            "High temperature today. "
            "Irrigate early morning or evening."
        )

    return (
        "Weather conditions are favorable "
        "for normal farming activities."
    )