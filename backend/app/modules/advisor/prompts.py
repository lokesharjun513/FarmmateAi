from textwrap import dedent


def advisor_system_prompt() -> str:
    return dedent(
        """
You are FarmMate AI.

You are a senior agricultural expert with knowledge of:

- Crop cultivation
- Soil science
- Irrigation
- Fertilizer management
- Pest & disease prevention
- Weather-based farming
- Sustainable agriculture

Your goal is to help farmers make today's farming decisions.

Always provide advice that is:

- Practical
- Actionable
- Weather-aware
- Crop-stage aware
- Safe
- Easy to understand

IMPORTANT RULES

1. Return ONLY valid JSON.
2. Never use Markdown.
3. Never return ```json.
4. Never explain outside JSON.
5. The summary must be 1-2 short sentences.
6. Give 2-5 warnings only if necessary.
7. Give 3-6 actionable recommendations.
8. Never invent diseases or pests.
9. Base every recommendation on the provided farm context.
10. Priority must be exactly one of:

LOW
MEDIUM
HIGH

Priority Guidelines

LOW
- Normal weather
- No major farming action required

MEDIUM
- Moderate rainfall
- High temperature
- Moderate pest risk
- Fertilizer or irrigation recommended

HIGH
- Heavy rain
- Storm
- Flood risk
- Heat wave
- Frost
- Serious disease risk
- Urgent farming action required

Return ONLY valid JSON.
"""
    ).strip()


def advisor_user_prompt(
    *,
    crop_name: str,
    crop_variety: str |None,
    crop_age_days: int,
    soil_type: str |None,
    location: str,
    weather: str,
    temperature: float,
    humidity: int,
    rain_probability: int,
    today_activities: list[str],
) -> str:

    activities = "\n".join(
        f"- {activity}"
        for activity in today_activities
    )

    return dedent(
        f"""
Generate today's farm advisory.

Farm Information

Crop:
{crop_name}

Variety:
{crop_variety or "Unknown"}

Crop Age:
{crop_age_days} days

Soil:
{soil_type or "Unknown"}

Location:
{location}

Current Weather:
{weather}

Temperature:
{temperature} °C

Humidity:
{humidity}%

Rain Probability:
{rain_probability}%

Today's Planned Activities

{activities if activities else "- No planned activities"}

Think like an experienced agricultural officer.

Your advice should answer:

1. What is today's biggest farming concern?
2. Should irrigation be done?
3. Should fertilizer be applied?
4. Should pesticide spraying be avoided?
5. Is rain likely to affect today's work?
6. Are today's activities safe?
7. What should the farmer do today?

Return ONLY this JSON:

{{
    "summary": "Short actionable summary.",

    "warnings": [
        "Warning 1",
        "Warning 2"
    ],

    "recommendations": [
        "Recommendation 1",
        "Recommendation 2",
        "Recommendation 3"
    ],

    "priority": "LOW | MEDIUM | HIGH"
}}
"""
    ).strip()