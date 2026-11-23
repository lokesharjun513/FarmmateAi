from datetime import date
from uuid import UUID

from app.modules.ai_engine.recommendation_context import RecommendationContext

from app.modules.farm.models import Farm
from app.modules.farm.repository import FarmRepository

from app.modules.master.seasons import (
    get_current_farming_season,
)

from app.modules.weather.service import WeatherService

from app.shared.exceptions import ValidationError


class RecommendationContextBuilder:

    def __init__(
        self,
        *,
        farm_repository: FarmRepository,
        weather_service: WeatherService,
    ):
        self.farm_repository = farm_repository
        self.weather_service = weather_service

    async def build(
        self,
        farm_id: UUID,
    ) -> RecommendationContext:

        farm = self.farm_repository.get_by_id(
            farm_id,
        )

        if farm is None:
            raise ValidationError(
                "Farm not found."
            )

        if (
            farm.latitude is None
            or farm.longitude is None
        ):
            raise ValidationError(
                "Farm location is required."
            )

        location = self._build_location(
            farm,
        )

        weather = (await self.weather_service.get_current_weather(
            latitude=farm.latitude,
            longitude=farm.longitude,
            location=location,
        )).data

        return RecommendationContext(
            state=farm.state,
            district=farm.district,
            mandal=farm.mandal,
            village=farm.village,
            season=self._get_current_season(),
            land_area=farm.land_area,
            land_unit=farm.land_unit,
            soil_type=farm.soil_type,
            water_source=farm.water_source,
            water_availability=farm.water_availability,
            irrigation_method=farm.irrigation_method,
            latitude=farm.latitude,
            longitude=farm.longitude,
            weather=weather,
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

    def _get_current_season(
        self,
    ) -> str:

        return get_current_farming_season(
            date.today().month,
        ).value