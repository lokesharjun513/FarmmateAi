from app.modules.ai_engine.parser import AIResponseParser

response = """
```json
{
    "crop_name": "Paddy",
    "crop_variety": "BPT-5204",
    "season": "Kharif",
    "estimated_duration_days": 130,
    "stages": [
        {
            "name": "Land Preparation",
            "description": "Prepare the field for paddy cultivation.",
            "stage_order": 1,
            "start_day": 1,
            "end_day": 7,
            "activities": [
                {
                    "day": 1,
                    "title": "Land Preparation",
                    "activity_type": "OTHER",
                    "description": "Prepare the field.",
                    "priority": "HIGH",
                    "estimated_duration_minutes": 180
                }
            ]
        }
    ]
}
```
"""

plan = AIResponseParser.parse_crop_plan(response)

print("\n===== Crop Plan =====")
print(plan)

print("\nCrop:", plan.crop_name)
print("Variety:", plan.crop_variety)
print("Season:", plan.season)
print("Duration:", plan.estimated_duration_days)

print("\nStages:", len(plan.stages))

print("\nFirst Stage:")
print(plan.stages[0])

print("\nActivities in First Stage:")
print(len(plan.stages[0].activities))

print("\nFirst Activity:")
print(plan.stages[0].activities[0])
