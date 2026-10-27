from app.modules.ai_engine.parser import AIResponseParser

response = """
{
    "summary": "Apply fertilizer before noon.",

    "warnings": [
        "Rain expected after 3 PM."
    ],

    "recommendations": [
        "Skip irrigation today.",
        "Monitor water level."
    ],

    "priority": "HIGH"
}
"""

advice = AIResponseParser.parse_daily_advice(response)

print(advice)