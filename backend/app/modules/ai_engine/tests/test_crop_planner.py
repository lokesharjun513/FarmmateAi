import json

import pytest

from app.core.config import settings
from app.modules.ai_engine.planner import CropPlanner


class FakeAIProvider:
    def __init__(self):
        self.kwargs = None

    async def generate(self, **kwargs):
        self.kwargs = kwargs
        return json.dumps(
            {
                "crop_name": "Sorghum",
                "crop_variety": None,
                "season": "ZAID",
                "estimated_duration_days": 100,
                "stages": [
                    {
                        "name": "Sowing",
                        "description": "Sow the crop.",
                        "stage_order": 1,
                        "start_day": 1,
                        "end_day": 10,
                        "activities": [
                            {
                                "day": 1,
                                "title": "Sow seeds",
                                "activity_type": "SOWING",
                                "description": "Sow treated seeds.",
                                "priority": "HIGH",
                                "estimated_duration_minutes": 60,
                            }
                        ],
                    }
                ],
            }
        )


@pytest.mark.asyncio
async def test_crop_planner_uses_dedicated_output_token_limit():
    planner = CropPlanner()
    provider = FakeAIProvider()
    planner.provider = provider

    plan = await planner.generate(
        crop_name="Sorghum",
        crop_variety=None,
        season="ZAID",
        state="Andhra Pradesh",
        district="Nellore",
        village="Vasili",
        land_area=3.0,
        land_unit="Acres",
        soil_type="Black Soil",
    )

    assert provider.kwargs is not None
    assert provider.kwargs["max_tokens"] == settings.CROP_PLAN_MAX_TOKENS
    assert settings.CROP_PLAN_MAX_TOKENS >= 6000
    assert plan.crop_name == "Sorghum"
