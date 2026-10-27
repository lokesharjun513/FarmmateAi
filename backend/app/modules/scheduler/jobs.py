import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database.session import SessionLocal

from app.modules.activity.repository import ActivityRepository
from app.modules.chat.session_repository import SessionRepository
from app.modules.crop_season.repository import CropSeasonRepository
from app.modules.farm.repository import FarmRepository
from app.modules.farmer.repository import FarmerRepository
from app.modules.notifications.repository import NotificationRepository
from app.modules.scheduler.service import SchedulerService


logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_scheduler_job():

    db = SessionLocal()

    try:

        service = SchedulerService(
            farm_repository=FarmRepository(db),
            farmer_repository=FarmerRepository(db),
            crop_repository=CropSeasonRepository(db),
            activity_repository=ActivityRepository(db),
            notification_repository=NotificationRepository(db),
            session_repository=SessionRepository(db),
        )

        result = await service.run()

        logger.info(
            "Scheduler completed successfully: %s",
            result.model_dump(),
        )

    except Exception:

        logger.exception(
            "Scheduler execution failed.",
        )

    finally:

        db.close()


def start_scheduler():

    #
    # Prevent duplicate scheduler when using uvicorn --reload
    #

    if scheduler.running:
        return

    #
    # Development
    #
    # scheduler.add_job(
    #     run_scheduler_job,
    #     trigger="interval",
    #     minutes=1,
    #     id="farmmate_scheduler",
    #     replace_existing=True,
    # )

    #
    # Production
    #

    scheduler.add_job(
        run_scheduler_job,
        trigger="cron",
        hour=6,
        minute=0,
        id="farmmate_scheduler",
        replace_existing=True,
    )

    scheduler.start()

    logger.info("Scheduler started.")