from datetime import datetime, timezone
import logging

from app.modules.activity.repository import ActivityRepository
from app.modules.advisor.service import AdvisorService
from app.modules.chat.session_repository import SessionRepository
from app.modules.crop_season.repository import CropSeasonRepository
from app.modules.farm.repository import FarmRepository
from app.modules.farmer.repository import FarmerRepository
from app.modules.notifications.models import (
    Notification,
    NotificationPriority,
    NotificationType,
)
from app.modules.notifications.repository import NotificationRepository
from app.modules.scheduler.schemas import SchedulerRunResponse
from app.modules.weather.service import WeatherService


logger = logging.getLogger(__name__)


class SchedulerService:

    def __init__(
        self,
        *,
        farm_repository: FarmRepository,
        farmer_repository: FarmerRepository,
        crop_repository: CropSeasonRepository,
        activity_repository: ActivityRepository,
        notification_repository: NotificationRepository,
        session_repository: SessionRepository,
    ):
        self.farm_repository = farm_repository
        self.farmer_repository = farmer_repository
        self.crop_repository = crop_repository
        self.activity_repository = activity_repository
        self.notification_repository = notification_repository
        self.session_repository = session_repository

        self.weather_service = WeatherService()

        self.advisor_service = AdvisorService(
            farm_repository=farm_repository,
            crop_repository=crop_repository,
            activity_repository=activity_repository,
        )

    async def run(
        self,
    ) -> SchedulerRunResponse:

        processed_farms = 0
        processed_crop_seasons = 0
        weather_updated = 0
        advisor_generated = 0
        notifications_created = 0

        farms = self.farm_repository.get_all()

        for farm in farms:

            processed_farms += 1

            # ====================================================
            # ACTIVE CROP
            # ====================================================

            crop = self.crop_repository.get_active_by_farm(
                farm.id,
            )

            if crop is None:
                continue

            processed_crop_seasons += 1

            # ====================================================
            # WEATHER
            # ====================================================

            if (
                farm.latitude is not None
                and farm.longitude is not None
            ):

                try:

                    await self.weather_service.get_current_weather(
                        latitude=farm.latitude,
                        longitude=farm.longitude,
                        location=f"{farm.village}, {farm.district}",
                    )

                    weather_updated += 1

                except Exception:

                    logger.exception(
                        "Weather update failed for farm %s",
                        farm.id,
                    )

            # ====================================================
            # FARMER
            # ====================================================

            farmer = self.farmer_repository.get_by_id(
                farm.farmer_id,
            )

            if farmer is None:

                logger.warning(
                    "Farmer not found for farm %s",
                    farm.id,
                )

                continue

            # ====================================================
            # AI ADVISOR
            # ====================================================

            try:

                advice = await self.advisor_service.get_today_advice(
                    farmer,
                )

                advisor_generated += 1

                # ------------------------------------------------
                # Create unread AI advisor notification
                # ------------------------------------------------

                notification = Notification(
                    farmer_id=farmer.id,
                    title="Today's AI Advice",
                    message=advice.summary,
                    type=NotificationType.AI_ADVISOR,
                    priority=NotificationPriority.MEDIUM,
                    is_read=False,
                )

                self.notification_repository.create(
                    notification,
                )

                notifications_created += 1

                logger.info(
                    "Advisor notification created for farmer %s",
                    farmer.id,
                )

            except Exception:

                logger.exception(
                    "Advisor generation failed for farmer %s",
                    farmer.id,
                )

                continue

        # ========================================================
        # CLEANUP EXPIRED ASK FM SESSIONS
        # ========================================================

        expired_sessions = (
            self.session_repository.delete_expired_sessions(
                datetime.now(timezone.utc),
            )
        )

        # ========================================================
        # SCHEDULER SUMMARY
        # ========================================================

        logger.info(
            "Scheduler Summary | "
            "Farms=%s Crops=%s Weather=%s Advisor=%s "
            "Notifications=%s ExpiredSessions=%s",
            processed_farms,
            processed_crop_seasons,
            weather_updated,
            advisor_generated,
            notifications_created,
            expired_sessions,
        )

        # ========================================================
        # RESPONSE
        # ========================================================

        return SchedulerRunResponse(
            processed_farms=processed_farms,
            processed_crop_seasons=processed_crop_seasons,
            weather_updated=weather_updated,
            advisor_generated=advisor_generated,
            notifications_created=notifications_created,
            expired_sessions=expired_sessions,
            completed=True,
        )