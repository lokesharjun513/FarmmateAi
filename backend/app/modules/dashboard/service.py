from datetime import date, datetime
from typing import Any

from app.modules.activity.models import ActivityStatus
from app.modules.activity.repository import ActivityRepository

from app.modules.advisor.service import AdvisorService

from app.modules.chat.session_repository import SessionRepository

from app.modules.crop_season.models import CropSeason
from app.modules.crop_season.repository import CropSeasonRepository

from app.modules.crop_stage.models import CropStage
from app.modules.crop_stage.repository import CropStageRepository

from app.modules.dashboard.schemas import (
    ActivityItem,
    AdvisorCard,
    AskFMCard,
    CropCard,
    CropStageCard,
    DashboardResponse,
    DashboardStats,
    FarmCard,
    FarmerCard,
    WeatherCard,
)

from app.modules.farm.repository import FarmRepository
from app.modules.farmer.models import Farmer
from app.modules.weather.service import WeatherService


class DashboardService:

    def __init__(
        self,
        *,
        farm_repository: FarmRepository,
        crop_repository: CropSeasonRepository,
        crop_stage_repository: CropStageRepository,
        activity_repository: ActivityRepository,
        session_repository: SessionRepository,
        weather_service: WeatherService,
        advisor_service: AdvisorService,
    ):
        self.farm_repository = farm_repository
        self.crop_repository = crop_repository
        self.crop_stage_repository = crop_stage_repository
        self.activity_repository = activity_repository
        self.session_repository = session_repository
        self.weather_service = weather_service
        self.advisor_service = advisor_service

    # ========================================================
    # PROGRESS
    # ========================================================

    @staticmethod
    def calculate_progress(
        crop_age_days: int,
        estimated_duration_days: int,
    ) -> int:

        if estimated_duration_days <= 0:
            return 0

        progress = int(
            crop_age_days * 100 / estimated_duration_days
        )

        return max(
            0,
            min(progress, 100),
        )

    # ========================================================
    # GREETING
    # ========================================================

    @staticmethod
    def get_greeting() -> str:

        hour = datetime.now().hour

        if hour < 12:
            return "Good Morning"

        if hour < 17:
            return "Good Afternoon"

        return "Good Evening"

    # ========================================================
    # CROP AGE
    # ========================================================

    @staticmethod
    def calculate_crop_age(
        crop: CropSeason,
        today: date,
    ) -> int:

        if crop.sowing_date is None:
            return 0

        return max(
            0,
            (today - crop.sowing_date).days,
        )

    # ========================================================
    # ESTIMATED DURATION
    # ========================================================

    @staticmethod
    def calculate_estimated_duration(
        crop: CropSeason,
    ) -> int:

        if (
            crop.sowing_date is not None
            and crop.expected_harvest_date is not None
        ):

            duration = (
                crop.expected_harvest_date
                - crop.sowing_date
            ).days

            return max(
                duration,
                1,
            )

        # Safe fallback.

        return 120

    # ========================================================
    # STAGE → CARD
    # ========================================================

    @staticmethod
    def _stage_to_card(
        stage: CropStage | None,
    ) -> CropStageCard | None:

        if stage is None:
            return None

        return CropStageCard(
            id=str(stage.id),
            name=stage.name,
            description=stage.description,
            stage_order=stage.stage_order,
            start_day=stage.start_day,
            end_day=stage.end_day,
            status=stage.status.value,
            started_at=(
                str(stage.started_at)
                if stage.started_at is not None
                else None
            ),
            completed_at=(
                str(stage.completed_at)
                if stage.completed_at is not None
                else None
            ),
        )

    # ========================================================
    # GET CURRENT STAGE
    # ========================================================

    def _get_current_stage(
        self,
        crop: CropSeason,
    ) -> CropStage | None:

        return (
            self.crop_stage_repository
            .get_active_by_crop_season(
                crop.id,
            )
        )

    # ========================================================
    # GET NEXT STAGE
    # ========================================================

    def _get_next_stage(
        self,
        current_stage: CropStage | None,
        crop: CropSeason,
    ) -> CropStage | None:

        if current_stage is None:
            return (
                self.crop_stage_repository
                .get_first_pending_stage(
                    crop.id,
                )
            )

        return (
            self.crop_stage_repository
            .get_next_stage(
                crop_season_id=crop.id,
                current_stage_order=current_stage.stage_order,
            )
        )

    # ========================================================
    # CROP CARD
    # ========================================================

    def _build_crop_card(
        self,
        crop: CropSeason,
        today: date,
    ) -> CropCard:

        crop_age_days = self.calculate_crop_age(
            crop,
            today,
        )

        estimated_duration_days = (
            self.calculate_estimated_duration(
                crop,
            )
        )

        progress_percentage = self.calculate_progress(
            crop_age_days=crop_age_days,
            estimated_duration_days=estimated_duration_days,
        )

        current_stage = self._get_current_stage(
            crop,
        )

        next_stage = self._get_next_stage(
            current_stage=current_stage,
            crop=crop,
        )

        return CropCard(
            id=str(crop.id),

            crop_name=crop.crop_name,

            crop_variety=crop.crop_variety,

            season=crop.season.value,

            year=crop.year,

            status=crop.status.value,

            is_active=crop.is_active,

            sowing_date=str(crop.sowing_date),

            expected_harvest_date=(
                str(crop.expected_harvest_date)
                if crop.expected_harvest_date is not None
                else None
            ),

            harvested_date=(
                str(crop.harvested_date)
                if crop.harvested_date is not None
                else None
            ),

            land_area=float(
                crop.land_area,
            ),

            land_unit=crop.land_unit,

            crop_age_days=crop_age_days,

            estimated_duration_days=estimated_duration_days,

            progress_percentage=progress_percentage,

            current_stage=self._stage_to_card(
                current_stage,
            ),

            next_stage=self._stage_to_card(
                next_stage,
            ),
        )

    # ========================================================
    # WEATHER
    # ========================================================

    async def _get_weather(
        self,
        farm: Any,
    ) -> WeatherCard:

        unavailable = WeatherCard(
            temperature=0,
            humidity=0,
            condition="Unavailable",
            rain_probability=None,
            is_available=False,
        )

        if (
            farm.latitude is None
            or farm.longitude is None
        ):
            return unavailable

        try:

            weather = (
                await self.weather_service
                .get_current_weather(
                    latitude=farm.latitude,
                    longitude=farm.longitude,
                    location=(
                        f"{farm.village}, "
                        f"{farm.district}"
                    ),
                )
            )

            return WeatherCard(
                temperature=float(
                    weather.temperature,
                ),
                humidity=int(
                    weather.humidity,
                ),
                condition=weather.weather_condition,
                rain_probability=(
                    int(weather.rain_probability)
                    if weather.rain_probability is not None
                    else None
                ),
                is_available=True,
            )

        except Exception:

            return unavailable

    # ========================================================
    # ADVISOR
    # ========================================================

    async def _get_advisor(
        self,
        current_farmer: Farmer,
    ) -> AdvisorCard:

        try:

            advisor = (
                await self.advisor_service
                .get_today_advice(
                    current_farmer,
                )
            )

            return AdvisorCard(
                summary=advisor.summary,
                priority=advisor.priority,
                available=True,
            )

        except Exception:

            return AdvisorCard(
                summary=(
                    "FarmMate AI recommendations "
                    "are temporarily unavailable."
                ),
                priority="LOW",
                available=False,
            )

    # ========================================================
    # ACTIVITY PRIORITY
    # ========================================================

    @staticmethod
    def _priority_value(
        activity: Any,
    ) -> str:

        priority = activity.priority

        return (
            priority.value
            if hasattr(priority, "value")
            else str(priority)
        )

    # ========================================================
    # ACTIVITY STATUS
    # ========================================================

    @staticmethod
    def _status_value(
        activity: Any,
    ) -> str:

        status = activity.status

        return (
            status.value
            if hasattr(status, "value")
            else str(status)
        )

    # ========================================================
    # ACTIVITY → CARD
    # ========================================================

    @classmethod
    def _activity_to_card(
        cls,
        activity: Any,
    ) -> ActivityItem:

        activity_type = activity.activity_type

        if hasattr(
            activity_type,
            "value",
        ):
            activity_type = activity_type.value

        return ActivityItem(
            id=str(activity.id),

            title=activity.title,

            description=activity.description,

            activity_type=str(
                activity_type,
            ),

            priority=cls._priority_value(
                activity,
            ),

            status=cls._status_value(
                activity,
            ),

            scheduled_date=str(
                activity.scheduled_date,
            ),

            completed_date=(
                str(activity.completed_date)
                if activity.completed_date is not None
                else None
            ),

            source=(
                activity.source.value
                if hasattr(
                    activity.source,
                    "value",
                )
                else str(activity.source)
                if activity.source is not None
                else None
            ),
        )

    # ========================================================
    # SORT ACTIVITIES
    # ========================================================

    @classmethod
    def _sort_activities(
        cls,
        activities: list[Any],
    ) -> list[Any]:

        priority_order = {
            "HIGH": 0,
            "MEDIUM": 1,
            "LOW": 2,
        }

        status_order = {
            "IN_PROGRESS": 0,
            "PENDING": 1,
            "COMPLETED": 2,
            "SKIPPED": 3,
        }

        return sorted(
            activities,
            key=lambda activity: (
                status_order.get(
                    cls._status_value(activity),
                    4,
                ),
                priority_order.get(
                    cls._priority_value(activity),
                    3,
                ),
                activity.scheduled_date,
            ),
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    @classmethod
    def _build_stats(
        cls,
        all_activities: list[Any],
        today_activities: list[Any],
    ) -> DashboardStats:

        def count_status(
            activities: list[Any],
            status: ActivityStatus,
        ) -> int:

            return sum(
                1
                for activity in activities
                if activity.status == status
            )

        return DashboardStats(

            total_tasks=len(
                all_activities,
            ),

            pending_tasks=count_status(
                all_activities,
                ActivityStatus.PENDING,
            ),

            in_progress_tasks=count_status(
                all_activities,
                ActivityStatus.IN_PROGRESS,
            ),

            completed_tasks=count_status(
                all_activities,
                ActivityStatus.COMPLETED,
            ),

            skipped_tasks=count_status(
                all_activities,
                ActivityStatus.SKIPPED,
            ),

            today_tasks=len(
                today_activities,
            ),

            today_completed_tasks=count_status(
                today_activities,
                ActivityStatus.COMPLETED,
            ),

            today_pending_tasks=count_status(
                today_activities,
                ActivityStatus.PENDING,
            ),

            today_in_progress_tasks=count_status(
                today_activities,
                ActivityStatus.IN_PROGRESS,
            ),
        )

    # ========================================================
    # MAIN DASHBOARD
    # ========================================================

    async def get_dashboard(
        self,
        current_farmer: Farmer,
    ) -> DashboardResponse:

        today = date.today()

        # ----------------------------------------------------
        # FARM
        # ----------------------------------------------------

        farms = (
            self.farm_repository
            .get_all_by_farmer(
                current_farmer.id,
            )
        )

        farm = next(
            (
                item
                for item in farms
                if item.is_primary
            ),
            farms[0] if farms else None,
        )

        # ----------------------------------------------------
        # DEFAULT VALUES
        # ----------------------------------------------------

        active_crop = None

        weather_card = WeatherCard(
            temperature=0,
            humidity=0,
            condition="Unavailable",
            rain_probability=None,
            is_available=False,
        )

        advisor_card = AdvisorCard(
            summary=(
                "No recommendation available."
            ),
            priority="LOW",
            available=False,
        )

        activities_card: list[
            ActivityItem
        ] = []

        stats = DashboardStats(
            total_tasks=0,
            pending_tasks=0,
            in_progress_tasks=0,
            completed_tasks=0,
            skipped_tasks=0,
            today_tasks=0,
            today_completed_tasks=0,
            today_pending_tasks=0,
            today_in_progress_tasks=0,
        )

        ask_fm_card = AskFMCard(
            active_session=False,
        )

        # ----------------------------------------------------
        # ASK FARMATE
        # ----------------------------------------------------

        session = (
            self.session_repository
            .get_active_session(
                current_farmer.id,
            )
        )

        if session is not None:

            ask_fm_card = AskFMCard(
                active_session=True,
            )

        # ----------------------------------------------------
        # FARM DATA
        # ----------------------------------------------------

        if farm is None:

            return DashboardResponse(
                greeting=self.get_greeting(),

                farmer=FarmerCard(
                    id=str(
                        current_farmer.id,
                    ),
                    full_name=(
                        current_farmer
                        .user
                        .full_name
                    ),
                    preferred_language=(
                        current_farmer
                        .preferred_language
                    ),
                ),

                farm=None,

                active_crop=None,

                weather=weather_card,

                advisor=advisor_card,

                stats=stats,

                activities=[],

                ask_fm=ask_fm_card,
            )

        # ----------------------------------------------------
        # WEATHER
        # ----------------------------------------------------

        weather_card = await self._get_weather(
            farm,
        )

        # ----------------------------------------------------
        # ACTIVE CROP
        # ----------------------------------------------------

        crop = (
            self.crop_repository
            .get_active_by_farm(
                farm.id,
            )
        )

        if crop is not None:

            active_crop = self._build_crop_card(
                crop,
                today,
            )

            # ------------------------------------------------
            # TODAY'S ACTIVITIES
            # ------------------------------------------------

            today_activities = (
                self.activity_repository
                .get_today_activities(
                    crop.id,
                    today,
                )
            )

            today_activities = (
                self._sort_activities(
                    today_activities,
                )
            )

            activities_card = [
                self._activity_to_card(
                    activity,
                )
                for activity in today_activities
            ]

            # ------------------------------------------------
            # ALL ACTIVITIES
            # ------------------------------------------------

            all_activities = (
                self.activity_repository
                .get_all_by_crop_season(
                    crop.id,
                )
            )

            stats = self._build_stats(
                all_activities=all_activities,
                today_activities=today_activities,
            )

            # ------------------------------------------------
            # AI ADVISOR
            # ------------------------------------------------

            advisor_card = await self._get_advisor(
                current_farmer,
            )

        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        return DashboardResponse(

            greeting=self.get_greeting(),

            farmer=FarmerCard(
                id=str(
                    current_farmer.id,
                ),
                full_name=(
                    current_farmer
                    .user
                    .full_name
                ),
                preferred_language=(
                    current_farmer
                    .preferred_language
                ),
            ),

            farm=FarmCard(
                id=str(
                    farm.id,
                ),

                farm_name=farm.farm_name,

                village=farm.village,
                mandal=farm.mandal,
                district=farm.district,
                state=farm.state,

                soil_type=farm.soil_type,

                water_source=farm.water_source,
                water_availability=(
                    farm.water_availability
                ),
                irrigation_method=(
                    farm.irrigation_method
                ),

                land_area=float(
                    farm.land_area,
                ),

                land_unit=farm.land_unit,
            ),

            active_crop=active_crop,

            weather=weather_card,

            advisor=advisor_card,

            stats=stats,

            activities=activities_card,

            ask_fm=ask_fm_card,
        )