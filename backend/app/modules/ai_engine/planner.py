from app.core.config import settings
from app.modules.ai_engine.parser import (
    AIResponseParser,
)
from app.modules.ai_engine.prompts import (
    crop_planner_system_prompt,
    crop_planner_user_prompt,
)
from app.modules.ai_engine.providers.ai_provider import (
    AIProvider,
)
from app.modules.crop_planner.schemas import (
    CropPlanResponse,
)


class CropPlanner:

    def __init__(self):

        self.provider = AIProvider()

    # ========================================================
    # GENERATE CROP PLAN
    # ========================================================

    async def generate(
        self,
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
    ) -> CropPlanResponse:

        # ----------------------------------------------------
        # System prompt
        # ----------------------------------------------------

        system_prompt = (
            crop_planner_system_prompt()
        )

        # ----------------------------------------------------
        # User prompt
        # ----------------------------------------------------

        user_prompt = (
            crop_planner_user_prompt(
                crop_name=crop_name,
                crop_variety=crop_variety,
                season=season,
                state=state,
                district=district,
                village=village,
                land_area=land_area,
                land_unit=land_unit,
                soil_type=soil_type,
            )
        )

        # ----------------------------------------------------
        # Call AI provider
        # ----------------------------------------------------

        response = await self.provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=settings.CROP_PLAN_MAX_TOKENS,
        )

        # ----------------------------------------------------
        # Parse + validate AI response
        # ----------------------------------------------------

        return AIResponseParser.parse_crop_plan(
            response,
        )