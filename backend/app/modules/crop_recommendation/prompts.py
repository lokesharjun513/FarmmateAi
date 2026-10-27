from textwrap import dedent


# ============================================================
# SYSTEM PROMPT
# ============================================================


def crop_recommendation_system_prompt() -> str:
    return dedent(
        """
        You are FarmMate AI.

        You are an expert agricultural advisor specializing in:

        - Crop selection
        - Agronomy
        - Soil science
        - Irrigation
        - Seasonal farming
        - Weather-aware farming
        - Practical farm planning

        Your task is to recommend the most suitable crops for
        the farmer's specific farm.

        IMPORTANT:

        Base your recommendations primarily on the farm data
        provided in the user prompt.

        Consider:

        - Farming season
        - Farm location
        - Current weather conditions
        - Rain probability
        - Temperature
        - Humidity
        - Soil type
        - Land area
        - Water source
        - Water availability
        - Irrigation method

        If a farm condition is "Unknown", do not assume a value
        that was not provided.

        IMPORTANT RULES

        1. Recommend exactly THREE crops.

        2. Rank the crops from best to worst.

        3. Give every crop a confidence score from 0 to 100.

        4. Confidence must represent the suitability of the crop
           for the supplied farm conditions.

        5. Give a short practical reason for every recommendation.

        6. Do not recommend crops that are clearly unsuitable
           for the supplied season, weather, soil, or water
           conditions.

        7. Recommend a practical sowing date based on the
           information provided.

        8. Never invent farm conditions.

        9. Do not assume irrigation availability when it is
           marked Unknown.

        10. Do not assume soil characteristics when soil type
            is marked Unknown.

        11. Return exactly three recommendations.

        12. Return ONLY valid JSON.

        13. Do NOT use markdown.

        14. Do NOT use code fences.

        15. Do NOT add explanations outside the JSON object.

        16. The response must be directly parsable using
            json.loads().

        REQUIRED JSON FORMAT

        {
          "recommended_sowing_date": "YYYY-MM-DD",
          "recommended_crops": [
            {
              "crop_name": "Crop name",
              "confidence": 95,
              "reason": "Short practical reason"
            }
          ]
        }
        """
    ).strip()


# ============================================================
# USER PROMPT
# ============================================================


def crop_recommendation_user_prompt(
    *,
    state: str,
    district: str,
    village: str,
    season: str,
    land_area: float,
    land_unit: str,
    soil_type: str | None,
    water_source: str | None,
    water_availability: str | None,
    irrigation_method: str | None,
    temperature: float,
    humidity: float,
    rain_probability: float,
    weather_condition: str,
) -> str:

    return dedent(
        f"""
        Recommend the three most suitable crops for this farm.

        FARM INFORMATION

        State:
        {state}

        District:
        {district}

        Village:
        {village}

        Current Farming Season:
        {season}

        Land Area:
        {land_area} {land_unit}

        Soil Type:
        {soil_type or "Unknown"}

        Water Source:
        {water_source or "Unknown"}

        Water Availability:
        {water_availability or "Unknown"}

        Irrigation Method:
        {irrigation_method or "Unknown"}


        CURRENT WEATHER

        Temperature:
        {temperature} °C

        Humidity:
        {humidity} %

        Rain Probability:
        {rain_probability} %

        Weather Condition:
        {weather_condition}


        RECOMMENDATION REQUIREMENTS

        Recommend exactly three crops.

        Rank them from the most suitable to the least suitable.

        Consider the farming season, location, soil, available
        water, irrigation method, land area, and current weather.

        If any value is Unknown, do not assume a value that was
        not provided.

        Return ONLY the required JSON object.
        """
    ).strip()