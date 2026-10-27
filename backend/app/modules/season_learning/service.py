from app.modules.activity.repository import ActivityRepository
from app.modules.chat.session_repository import SessionRepository
from app.modules.crop_season.repository import CropSeasonRepository
from app.modules.farm.repository import FarmRepository
from app.modules.notification.repository import NotificationRepository
from app.modules.scheduler.activity_scheduler import ActivityScheduler
from app.modules.scheduler.advisor_scheduler import AdvisorScheduler
from app.modules.scheduler.cleanup_scheduler import CleanupScheduler
from app.modules.scheduler.notification_scheduler import NotificationScheduler
from app.modules.scheduler.schemas import SchedulerRunResponse
from app.modules.scheduler.weather_scheduler import WeatherScheduler
from app.modules.weather.service import WeatherService


class SchedulerService:

    def __init__(
        self,
        *,
        farm_repository: FarmRepository,
        crop_repository: CropSeasonRepository,
        activity_repository: ActivityRepository,
        notification_repository: NotificationRepository,
        session_repository: SessionRepository,
        weather_service: WeatherService,
    ):
        self.activity_scheduler = ActivityScheduler(
            crop_repository=crop_repository,
            activity_repository=activity_repository,
        )

        self.weather_scheduler = WeatherScheduler(
            farm_repository=farm_repository,
            weather_service=weather_service,
        )

        self.advisor_scheduler = AdvisorScheduler(
            farm_repository=farm_repository,
            crop_repository=crop_repository,
        )

        self.notification_scheduler = NotificationScheduler(
            notification_repository=notification_repository,
        )

        self.cleanup_scheduler = CleanupScheduler(
            session_repository=session_repository,
        )

    async def run(self) -> SchedulerRunResponse:

        weather_result = await self.weather_scheduler.run()

        activity_result = await self.activity_scheduler.run()

        advisor_result = await self.advisor_scheduler.run()

        notification_result = await self.notification_scheduler.run()

        cleanup_result = self.cleanup_scheduler.run()

        return SchedulerRunResponse(
            processed_farms=weather_result.processed_farms,
            active_crop_seasons=activity_result.active_crop_seasons,
            weather_updated=weather_result.weather_updated,
            activities_created=activity_result.activities_created,
            advisors_generated=advisor_result.advisors_generated,
            notifications_created=notification_result.notifications_created,
            expired_chat_sessions=cleanup_result.expired_chat_sessions,
            completed=True,
        )