from datetime import timedelta

from app.modules.activity.models import Activity
from app.modules.activity.repository import ActivityRepository

from app.modules.ai_engine.planner import CropPlanner

from app.modules.crop_season.models import CropSeason


class AIEngineService:
    def __init__(
        self,
        activity_repository: ActivityRepository,
    ):
        self.activity_repository = activity_repository
        self.planner = CropPlanner()

    async def generate_crop_plan(
        self,
        crop_season: CropSeason,
    ):

        farm = crop_season.farm

        plan = await self.planner.generate_crop_plan(
            crop_name=crop_season.crop_name,
            crop_variety=crop_season.crop_variety,
            season=crop_season.season.value,
            state=farm.state,
            district=farm.district,
            village=farm.village,
            land_area=farm.land_area,
            land_unit=farm.land_unit,
            soil_type=farm.soil_type,
        )

        activities: list[Activity] = []

        for item in plan.activities:

            activities.append(
                Activity(
                    crop_season_id=crop_season.id,
                    activity_type=item.activity_type,
                    title=item.title,
                    description=item.description,
                    scheduled_date=(
                        crop_season.sowing_date
                        + timedelta(days=item.day - 1)
                    ),
                )
            )

        self.activity_repository.create_many(
            activities,
        )

        return plan