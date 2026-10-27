from datetime import date

from app.modules.activity.repository import ActivityRepository
from app.modules.advisor.schemas import DailyAdvisorResponse
from app.modules.ai_engine.advisor_planner import AdvisorPlanner
from app.modules.ai_engine.context import AIContext
from app.modules.crop_season.repository import CropSeasonRepository
from app.modules.farm.repository import FarmRepository
from app.modules.farmer.models import Farmer
from app.modules.weather.service import WeatherService

from app.shared.exceptions import ValidationError


class AdvisorService:

    def __init__(
        self,
        farm_repository: FarmRepository,
        crop_repository: CropSeasonRepository,
        activity_repository: ActivityRepository,
    ):
        self.farm_repository = farm_repository
        self.crop_repository = crop_repository
        self.activity_repository = activity_repository

        self.weather_service = WeatherService()
        self.planner = AdvisorPlanner()

    async def get_today_advice(
        self,
        current_farmer: Farmer,
    ) -> DailyAdvisorResponse:

        farms = self.farm_repository.get_all_by_farmer(
            current_farmer.id,
        )

        if not farms:
            raise ValidationError(
                "Farmer has no farms."
            )

        farm = next(
            (
                farm
                for farm in farms
                if farm.is_primary
            ),
            farms[0],
        )

        if (
            farm.latitude is None
            or farm.longitude is None
        ):
            raise ValidationError(
                "Farm location is required to generate daily advice."
            )

        crop = self.crop_repository.get_active_by_farm(
            farm.id,
        )

        if crop is None:
            raise ValidationError(
                "No active crop season found."
            )

        crop_age_days = max(
            0,
            (date.today() - crop.sowing_date).days,
        )

        activities = (
            self.activity_repository.get_today_activities(
                crop.id,
                date.today(),
            )
        )

        location = ", ".join(
            filter(
                None,
                [
                    farm.village,
                    farm.district,
                ],
            )
        )

        weather = await self.weather_service.get_current_weather(
            latitude=farm.latitude,
            longitude=farm.longitude,
            location=location,
        )

        context = AIContext(
            crop_name=crop.crop_name,
            crop_variety=crop.crop_variety,
            crop_age_days=crop_age_days,
            soil_type=farm.soil_type,
            location=location,
            weather=weather.weather_condition,
            temperature=weather.temperature,
            humidity=weather.humidity or 0,
            rain_probability=weather.rain_probability or 0,
            today_activities=[
                activity.title
                for activity in activities
            ],
        )

        return await self.planner.generate_daily_advice(
            context=context,
        )