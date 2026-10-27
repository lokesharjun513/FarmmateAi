from app.modules.ai_engine.orchestrator import AIOrchestrator
from app.modules.ai_engine.recommendation_context import RecommendationContext

from app.modules.crop_recommendation.prompts import (
    crop_recommendation_system_prompt,
    crop_recommendation_user_prompt,
)


class RecommendationPlanner:

    def __init__(self):
        self.orchestrator = AIOrchestrator()

    async def recommend(
        self,
        *,
        context: RecommendationContext,
    ) -> str:

        system_prompt = crop_recommendation_system_prompt()

        user_prompt = crop_recommendation_user_prompt(
            state=context.state,
            district=context.district,
            village=context.village,
            season=context.season,
            land_area=context.land_area,
            land_unit=context.land_unit,
            soil_type=context.soil_type,
            water_source=context.water_source,
            water_availability=context.water_availability,
            irrigation_method=context.irrigation_method,
            temperature=context.weather.temperature,
            humidity=context.weather.humidity or 0,
            rain_probability=context.weather.rain_probability or 0,
            weather_condition=context.weather.weather_condition,
        )

        response = await self.orchestrator.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=700,
        )

        return response.strip()