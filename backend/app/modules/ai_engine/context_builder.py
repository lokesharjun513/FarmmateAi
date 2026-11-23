import logging
from datetime import UTC, date, datetime

from app.modules.activity.repository import ActivityRepository
from app.modules.ai_engine.context import AIContext
from app.modules.crop_season.repository import CropSeasonRepository
from app.modules.farm.models import Farm
from app.modules.farm.repository import FarmRepository
from app.modules.farmer.models import Farmer
from app.modules.weather.service import WeatherService

logger = logging.getLogger(__name__)


class AIContextBuilder:

    def __init__(
        self,
        *,
        farm_repository: FarmRepository,
        crop_repository: CropSeasonRepository,
        activity_repository: ActivityRepository,
        weather_service: WeatherService,
    ):
        self.farm_repository = farm_repository
        self.crop_repository = crop_repository
        self.activity_repository = activity_repository
        self.weather_service = weather_service

    async def build(
        self,
        current_farmer: Farmer,
    ) -> AIContext:
        # Compatibility for tests using SimpleNamespace without preferred_language
        preferred_language = getattr(current_farmer, 'preferred_language', 'English')

        farms = self.farm_repository.get_all_by_farmer(
            current_farmer.id,
        )

        if not farms:
            logger.warning(
                "No farms found for farmer %s; "
                "using limited AI context.",
                current_farmer.id,
            )

            return self._build_limited_context()

        farm = self._get_primary_farm(
            farms,
        )

        location = self._build_location(
            farm,
        ) or "Unknown"

        crop = self.crop_repository.get_active_by_farm(
            farm.id,
        )

        if crop is None:
            logger.warning(
                "No active crop season found for farm %s; "
                "using limited AI context.",
                farm.id,
            )

            crop_name = "Unknown"
            crop_variety = None
            crop_age_days = 0
            activities = []

        else:
            crop_name = crop.crop_name
            crop_variety = crop.crop_variety
            crop_age_days = self._get_crop_age(
                crop.sowing_date,
            )
            activities = (
                self.activity_repository.get_today_activities(
                    crop.id,
                    datetime.now(UTC).date(),
                )
            )

        weather = await self._get_weather(
            farm=farm,
            location=location,
        )

        if weather is None:
            weather_condition = "Unknown"
            temperature = 0.0
            humidity = 0
            rain_probability = 0

        else:
            weather_condition = weather.weather_condition
            temperature = weather.temperature
            humidity = weather.humidity or 0
            rain_probability = weather.rain_probability or 0

        return AIContext(
            crop_name=crop_name,
            crop_variety=crop_variety,
            crop_age_days=crop_age_days,
            soil_type=farm.soil_type,
            location=location,
            weather=weather_condition,
            temperature=temperature,
            humidity=humidity,
            rain_probability=rain_probability,
            today_activities=[
                activity.title
                for activity in activities
            ],
            language=preferred_language,
        )

    async def _get_weather(
        self,
        *,
        farm: Farm,
        location: str,
    ):

        if (
            farm.latitude is None
            or farm.longitude is None
        ):
            logger.warning(
                "Farm %s has no coordinates; "
                "continuing without weather.",
                farm.id,
            )

            return None

        try:
            return (
                await self.weather_service.get_current_weather(
                    latitude=farm.latitude,
                    longitude=farm.longitude,
                    location=location,
                )
            ).data

        except Exception:
            logger.exception(
                "Weather lookup failed for farm %s; "
                "continuing without weather.",
                farm.id,
            )

            return None

    @staticmethod
    def _build_limited_context() -> AIContext:

        return AIContext(
            crop_name="Unknown",
            crop_variety=None,
            crop_age_days=0,
            soil_type=None,
            location="Unknown",
            weather="Unknown",
            temperature=0.0,
            humidity=0,
            rain_probability=0,
            today_activities=[],
        )

    def _get_primary_farm(
        self,
        farms: list[Farm],
    ) -> Farm:

        return next(
            (
                farm
                for farm in farms
                if farm.is_primary
            ),
            farms[0],
        )

    def _get_crop_age(
        self,
        sowing_date: date,
    ) -> int:

        return max(
            0,
            (
                datetime.now(UTC).date()
                - sowing_date
            ).days,
        )

    def _build_location(
        self,
        farm: Farm,
    ) -> str:

        return ", ".join(
            filter(
                None,
                [
                    farm.village,
                    farm.mandal,
                    farm.district,
                    farm.state,
                ],
            )
        )