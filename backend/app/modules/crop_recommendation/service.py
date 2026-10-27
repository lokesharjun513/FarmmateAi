from uuid import UUID

from app.modules.ai_engine.recommendation_context_builder import (
    RecommendationContextBuilder,
)

from app.modules.ai_engine.recommendation_planner import (
    RecommendationPlanner,
)

from app.modules.crop_recommendation.parser import (
    RecommendationParser,
)

from app.modules.crop_recommendation.schemas import (
    CropRecommendationResponse,
)

from app.modules.farm.repository import FarmRepository

from app.modules.weather.service import WeatherService


class CropRecommendationService:

    def __init__(
        self,
        *,
        farm_repository: FarmRepository,
        weather_service: WeatherService,
    ):

        self.context_builder = (
            RecommendationContextBuilder(
                farm_repository=farm_repository,
                weather_service=weather_service,
            )
        )

        self.planner = RecommendationPlanner()

        self.parser = RecommendationParser()

    # ========================================================
    # GENERATE RECOMMENDATION
    # ========================================================

    async def recommend(
        self,
        *,
        farm_id: UUID,
    ) -> CropRecommendationResponse:

        # ----------------------------------------------------
        # Build farm + weather context
        # ----------------------------------------------------

        context = await self.context_builder.build(
            farm_id,
        )

        # ----------------------------------------------------
        # Generate AI response
        # ----------------------------------------------------

        ai_response = await self.planner.recommend(
            context=context,
        )

        # ----------------------------------------------------
        # Parse AI response
        #
        # farm_id is injected by the trusted backend rather
        # than trusting the AI to return it.
        # ----------------------------------------------------

        recommendation = self.parser.parse(
            ai_response,
            farm_id=farm_id,
        )

        return recommendation