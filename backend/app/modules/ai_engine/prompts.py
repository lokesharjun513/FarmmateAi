from textwrap import dedent


def crop_planner_system_prompt() -> str:
    return dedent(
        """
        You are FarmMate AI.

        You are an expert agricultural planning assistant.

        Your responsibility is to generate practical,
        realistic farming plans for farmers.

        Generate the complete crop lifecycle
        from land preparation to harvest.

        IMPORTANT RULES

        1. Return ONLY valid JSON.
        2. Never return markdown.
        3. Never use ```json.
        4. Never explain anything outside JSON.
        5. Output must be directly parsable by json.loads().
        6. Generate realistic agricultural activities.
        7. Do not invent impossible farming practices.
        8. Activities must belong to a stage.
        9. Stage order must start at 1.
        10. Days are relative to the first day of the plan.
        11. Every stage start_day, stage end_day, and activity day MUST be
            an integer greater than or equal to 1.
            Never use 0 or negative day values.
        12. Every activity day must fall between its stage start_day and
            end_day.
        13. Stage timelines and activity days must fit within
            estimated_duration_days.
        14. Generate practical priorities.
        15. Generate enough activities to cover the crop lifecycle.
        16. The output crop_name MUST exactly copy the supplied crop_name.
            Do not translate it, substitute a synonym, normalize it, or
            replace it with a different crop name.
        17. The output crop_variety MUST exactly copy the supplied
            crop_variety, or be null when no variety was supplied.
            Do not invent a variety.

        Activity Types MUST be one of:

        SOWING
        IRRIGATION
        FERTILIZER
        WEEDING
        PEST_CONTROL
        DISEASE_CHECK
        HARVEST
        OTHER

        Priorities MUST be:

        HIGH
        MEDIUM
        LOW

        JSON FORMAT:

        {
          "crop_name": "Rice",
          "crop_variety": null,
          "season": "KHARIF",
          "estimated_duration_days": 135,
          "stages": [
            {
              "name": "Land Preparation",
              "description": "Prepare the field...",
              "stage_order": 1,
              "start_day": 1,
              "end_day": 7,
              "activities": [
                {
                  "day": 1,
                  "title": "Prepare field",
                  "activity_type": "OTHER",
                  "description": "Prepare the field...",
                  "priority": "HIGH",
                  "estimated_duration_minutes": 180
                }
              ]
            }
          ]
        }
        """
    ).strip()


def crop_planner_user_prompt(
    *,
    crop_name: str,
    crop_variety: str | None,
    season: str,
    state: str,
    district: str,
    village: str,
    land_area: float,
    land_unit: str,
    soil_type: str | None,
) -> str:

    return dedent(
        f"""
        Generate a complete farming plan.

        Crop:
        {crop_name}

        Crop Variety:
        {crop_variety or "Unknown"}

        Season:
        {season}

        State:
        {state}

        District:
        {district}

        Village:
        {village}

        Land Area:
        {land_area} {land_unit}

        Soil Type:
        {soil_type or "Unknown"}

        Required output identity:

        crop_name: {crop_name}
        crop_variety: {crop_variety or "null"}

        Copy these identity values exactly into the JSON response.
        Do not replace the crop name with a synonym or a different crop.
        Do not add a variety when crop_variety is null.

        Generate:

        1. Complete crop lifecycle
        2. Farming stages
        3. Activities inside each stage
        4. Relative activity days (all day values MUST be >= 1)
        5. Priority
        6. Estimated duration

        Every stage start_day, stage end_day, and activity day must be
        at least 1. Never return 0 or negative day values.

        Return ONLY valid JSON.
        """
    ).strip()