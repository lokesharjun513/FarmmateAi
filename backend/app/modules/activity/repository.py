from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.activity.models import (
    Activity,
    ActivityPriority,
    ActivitySource,
    ActivityStatus,
)


class ActivityRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_by_id(
        self,
        activity_id: UUID,
    ) -> Activity | None:

        return (
            self.db.query(Activity)
            .filter(
                Activity.id == activity_id,
            )
            .first()
        )

    # ========================================================
    # GET BY CROP SEASON AND ID
    # ========================================================

    def get_by_crop_season_and_id(
        self,
        crop_season_id: UUID,
        activity_id: UUID,
    ) -> Activity | None:

        return (
            self.db.query(Activity)
            .filter(
                Activity.id == activity_id,
                Activity.crop_season_id == crop_season_id,
            )
            .first()
        )

    # ========================================================
    # GET ALL BY CROP SEASON
    # ========================================================

    def get_all_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
            )
            .order_by(
                Activity.scheduled_date.asc(),
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET ALL BY STAGE
    # ========================================================

    def get_all_by_stage(
        self,
        stage_id: UUID,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.stage_id == stage_id,
            )
            .order_by(
                Activity.scheduled_date.asc(),
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET BY STAGE AND STATUS
    # ========================================================

    def get_by_stage_and_status(
        self,
        stage_id: UUID,
        activity_status: ActivityStatus,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.stage_id == stage_id,
                Activity.status == activity_status,
            )
            .order_by(
                Activity.scheduled_date.asc(),
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET BY STATUS
    # ========================================================

    def get_by_status(
        self,
        crop_season_id: UUID,
        status: ActivityStatus,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.status == status,
            )
            .order_by(
                Activity.scheduled_date.asc(),
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET TODAY
    # ========================================================

    def get_today_activities(
        self,
        crop_season_id: UUID,
        today: date,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.scheduled_date == today,
            )
            .order_by(
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET TODAY INCOMPLETE
    # ========================================================

    def get_today_incomplete_activities(
        self,
        crop_season_id: UUID,
        today: date,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.scheduled_date == today,
                Activity.status.in_(
                    [
                        ActivityStatus.PENDING,
                        ActivityStatus.IN_PROGRESS,
                    ]
                ),
            )
            .order_by(
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET TODAY PENDING
    # ========================================================

    def get_today_pending_activities(
        self,
        crop_season_id: UUID,
        today: date,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.scheduled_date == today,
                Activity.status == ActivityStatus.PENDING,
            )
            .order_by(
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET TODAY IN PROGRESS
    # ========================================================

    def get_today_in_progress_activities(
        self,
        crop_season_id: UUID,
        today: date,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.scheduled_date == today,
                Activity.status == ActivityStatus.IN_PROGRESS,
            )
            .order_by(
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET TODAY COMPLETED
    # ========================================================

    def get_today_completed_activities(
        self,
        crop_season_id: UUID,
        today: date,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.completed_date == today,
                Activity.status == ActivityStatus.COMPLETED,
            )
            .order_by(
                Activity.completed_date.desc(),
                Activity.created_at.desc(),
            )
            .all()
        )

    # ========================================================
    # GET PENDING
    # ========================================================

    def get_pending_activities(
        self,
        crop_season_id: UUID,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.status == ActivityStatus.PENDING,
            )
            .order_by(
                Activity.scheduled_date.asc(),
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET IN PROGRESS
    # ========================================================

    def get_in_progress_activities(
        self,
        crop_season_id: UUID,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.status == ActivityStatus.IN_PROGRESS,
            )
            .order_by(
                Activity.scheduled_date.asc(),
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET COMPLETED
    # ========================================================

    def get_completed_activities(
        self,
        crop_season_id: UUID,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.status == ActivityStatus.COMPLETED,
            )
            .order_by(
                Activity.completed_date.desc(),
                Activity.created_at.desc(),
            )
            .all()
        )

    # ========================================================
    # GET SKIPPED
    # ========================================================

    def get_skipped_activities(
        self,
        crop_season_id: UUID,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.status == ActivityStatus.SKIPPED,
            )
            .order_by(
                Activity.completed_date.desc(),
                Activity.created_at.desc(),
            )
            .all()
        )

    # ========================================================
    # GET UPCOMING
    # ========================================================

    def get_upcoming_activities(
        self,
        crop_season_id: UUID,
        from_date: date,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.scheduled_date >= from_date,
                Activity.status.in_(
                    [
                        ActivityStatus.PENDING,
                        ActivityStatus.IN_PROGRESS,
                    ]
                ),
            )
            .order_by(
                Activity.scheduled_date.asc(),
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET OVERDUE
    # ========================================================

    def get_overdue_activities(
        self,
        crop_season_id: UUID,
        today: date,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.scheduled_date < today,
                Activity.status.in_(
                    [
                        ActivityStatus.PENDING,
                        ActivityStatus.IN_PROGRESS,
                    ]
                ),
            )
            .order_by(
                Activity.scheduled_date.asc(),
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET BY DATE RANGE
    # ========================================================

    def get_by_date_range(
        self,
        crop_season_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.scheduled_date >= start_date,
                Activity.scheduled_date <= end_date,
            )
            .order_by(
                Activity.scheduled_date.asc(),
                Activity.priority.desc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET BY SOURCE
    # ========================================================

    def get_by_source(
        self,
        crop_season_id: UUID,
        source: ActivitySource,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.source == source,
            )
            .order_by(
                Activity.scheduled_date.desc(),
                Activity.created_at.desc(),
            )
            .all()
        )

    # ========================================================
    # GET BY PRIORITY
    # ========================================================

    def get_by_priority(
        self,
        crop_season_id: UUID,
        priority: ActivityPriority,
    ) -> list[Activity]:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.priority == priority,
            )
            .order_by(
                Activity.scheduled_date.asc(),
                Activity.created_at.asc(),
            )
            .all()
        )

    # ========================================================
    # GET LATEST ACTIVITY
    # ========================================================

    def get_latest_activity(
        self,
        crop_season_id: UUID,
    ) -> Activity | None:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
            )
            .order_by(
                Activity.created_at.desc(),
            )
            .first()
        )

    # ========================================================
    # GET LATEST COMPLETED ACTIVITY
    # ========================================================

    def get_latest_completed_activity(
        self,
        crop_season_id: UUID,
    ) -> Activity | None:

        return (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.status == ActivityStatus.COMPLETED,
            )
            .order_by(
                Activity.completed_date.desc(),
                Activity.created_at.desc(),
            )
            .first()
        )

    # ========================================================
    # CREATE
    # ========================================================

    def create(
        self,
        activity: Activity,
    ) -> Activity:

        self.db.add(activity)

        self.db.commit()

        self.db.refresh(
            activity,
        )

        return activity

    # ========================================================
    # CREATE WITHOUT COMMIT
    # ========================================================

    def create_without_commit(
        self,
        activity: Activity,
    ) -> Activity:

        self.db.add(activity)

        self.db.flush()

        return activity

    # ========================================================
    # CREATE MANY
    # ========================================================

    def create_many(
        self,
        activities: list[Activity],
    ) -> list[Activity]:

        if not activities:
            return []

        self.db.add_all(activities)

        self.db.flush()

        return activities

    # ========================================================
    # CREATE MANY WITHOUT COMMIT
    # ========================================================

    def create_many_without_commit(
        self,
        activities: list[Activity],
    ) -> list[Activity]:

        return self.create_many(
            activities,
        )

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        activity: Activity,
    ) -> Activity:

        self.db.flush()

        self.db.commit()

        self.db.refresh(
            activity,
        )

        return activity

    # ========================================================
    # UPDATE WITHOUT COMMIT
    # ========================================================

    def update_without_commit(
        self,
        activity: Activity,
    ) -> Activity:

        self.db.flush()

        return activity

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        activity: Activity,
    ) -> None:

        self.db.delete(
            activity,
        )

        self.db.commit()

    # ========================================================
    # DELETE WITHOUT COMMIT
    # ========================================================

    def delete_without_commit(
        self,
        activity: Activity,
    ) -> None:

        self.db.delete(
            activity,
        )

        self.db.flush()

    # ========================================================
    # DELETE ALL BY CROP SEASON
    # ========================================================

    def delete_all_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> None:

        (
            self.db.query(Activity)
            .filter(
                Activity.crop_season_id == crop_season_id,
            )
            .delete(
                synchronize_session=False,
            )
        )

        self.db.flush()

    # ========================================================
    # COUNT ALL
    # ========================================================

    def count_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
            )
            .count()
        )

    # ========================================================
    # COUNT BY STATUS
    # ========================================================

    def count_by_status(
        self,
        crop_season_id: UUID,
        activity_status: ActivityStatus,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.status == activity_status,
            )
            .count()
        )

    # ========================================================
    # COUNT BY SOURCE
    # ========================================================

    def count_by_source(
        self,
        crop_season_id: UUID,
        source: ActivitySource,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.source == source,
            )
            .count()
        )

    # ========================================================
    # COUNT BY PRIORITY
    # ========================================================

    def count_by_priority(
        self,
        crop_season_id: UUID,
        priority: ActivityPriority,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.priority == priority,
            )
            .count()
        )

    # ========================================================
    # COUNT TODAY
    # ========================================================

    def count_today(
        self,
        crop_season_id: UUID,
        today: date,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.scheduled_date == today,
            )
            .count()
        )

    # ========================================================
    # COUNT TODAY PENDING
    # ========================================================

    def count_pending_today(
        self,
        crop_season_id: UUID,
        today: date,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.scheduled_date == today,
                Activity.status == ActivityStatus.PENDING,
            )
            .count()
        )

    # ========================================================
    # COUNT TODAY COMPLETED
    # ========================================================

    def count_completed_today(
        self,
        crop_season_id: UUID,
        today: date,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.completed_date == today,
                Activity.status == ActivityStatus.COMPLETED,
            )
            .count()
        )

    # ========================================================
    # COUNT TODAY SKIPPED
    # ========================================================

    def count_skipped_today(
        self,
        crop_season_id: UUID,
        today: date,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.completed_date == today,
                Activity.status == ActivityStatus.SKIPPED,
            )
            .count()
        )

    # ========================================================
    # COUNT OVERDUE
    # ========================================================

    def count_overdue(
        self,
        crop_season_id: UUID,
        today: date,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.scheduled_date < today,
                Activity.status.in_(
                    [
                        ActivityStatus.PENDING,
                        ActivityStatus.IN_PROGRESS,
                    ]
                ),
            )
            .count()
        )

    # ========================================================
    # COUNT BY STAGE
    # ========================================================

    def count_by_stage(
        self,
        stage_id: UUID,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.stage_id == stage_id,
            )
            .count()
        )

    # ========================================================
    # HAS ACTIVITIES BY STAGE
    # ========================================================

    def has_activities_by_stage(
        self,
        stage_id: UUID,
    ) -> bool:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.stage_id == stage_id,
            )
            .first()
            is not None
        )

    # ========================================================
    # COUNT UNFINISHED BY STAGE
    #
    # PENDING + IN_PROGRESS
    # ========================================================

    def count_unfinished_by_stage(
        self,
        stage_id: UUID,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.stage_id == stage_id,
                Activity.status.in_(
                    [
                        ActivityStatus.PENDING,
                        ActivityStatus.IN_PROGRESS,
                    ]
                ),
            )
            .count()
        )

    # ========================================================
    # HAS UNFINISHED BY STAGE
    # ========================================================

    def has_unfinished_by_stage(
        self,
        stage_id: UUID,
    ) -> bool:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.stage_id == stage_id,
                Activity.status.in_(
                    [
                        ActivityStatus.PENDING,
                        ActivityStatus.IN_PROGRESS,
                    ]
                ),
            )
            .first()
            is not None
        )

    # ========================================================
    # ALL FINISHED BY STAGE
    #
    # COMPLETED + SKIPPED = FINISHED
    # ========================================================

    def all_finished_by_stage(
        self,
        stage_id: UUID,
    ) -> bool:

        return not self.has_unfinished_by_stage(
            stage_id,
        )

    # ========================================================
    # COUNT FINISHED BY STAGE
    #
    # COMPLETED + SKIPPED
    # ========================================================

    def count_finished_by_stage(
        self,
        stage_id: UUID,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.stage_id == stage_id,
                Activity.status.in_(
                    [
                        ActivityStatus.COMPLETED,
                        ActivityStatus.SKIPPED,
                    ]
                ),
            )
            .count()
        )

    # ========================================================
    # COUNT COMPLETED BY STAGE
    # ========================================================

    def count_completed_by_stage(
        self,
        stage_id: UUID,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.stage_id == stage_id,
                Activity.status == ActivityStatus.COMPLETED,
            )
            .count()
        )

    # ========================================================
    # COUNT SKIPPED BY STAGE
    # ========================================================

    def count_skipped_by_stage(
        self,
        stage_id: UUID,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.stage_id == stage_id,
                Activity.status == ActivityStatus.SKIPPED,
            )
            .count()
        )

    # ========================================================
    # COUNT PENDING BY STAGE
    # ========================================================

    def count_pending_by_stage(
        self,
        stage_id: UUID,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.stage_id == stage_id,
                Activity.status == ActivityStatus.PENDING,
            )
            .count()
        )

    # ========================================================
    # COUNT IN PROGRESS BY STAGE
    # ========================================================

    def count_in_progress_by_stage(
        self,
        stage_id: UUID,
    ) -> int:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.stage_id == stage_id,
                Activity.status == ActivityStatus.IN_PROGRESS,
            )
            .count()
        )

    # ========================================================
    # EXISTS
    # ========================================================

    def exists(
        self,
        activity_id: UUID,
    ) -> bool:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.id == activity_id,
            )
            .first()
            is not None
        )

    # ========================================================
    # HAS IN-PROGRESS ACTIVITY
    # ========================================================

    def has_in_progress_activity(
        self,
        crop_season_id: UUID,
    ) -> bool:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.status == ActivityStatus.IN_PROGRESS,
            )
            .first()
            is not None
        )

    # ========================================================
    # HAS PENDING ACTIVITY
    # ========================================================

    def has_pending_activity(
        self,
        crop_season_id: UUID,
    ) -> bool:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.status == ActivityStatus.PENDING,
            )
            .first()
            is not None
        )

    # ========================================================
    # HAS UNFINISHED ACTIVITY
    #
    # PENDING + IN_PROGRESS
    # ========================================================

    def has_unfinished_activity(
        self,
        crop_season_id: UUID,
    ) -> bool:

        return (
            self.db.query(Activity.id)
            .filter(
                Activity.crop_season_id == crop_season_id,
                Activity.status.in_(
                    [
                        ActivityStatus.PENDING,
                        ActivityStatus.IN_PROGRESS,
                    ]
                ),
            )
            .first()
            is not None
        )

    # ========================================================
    # TRANSACTION: COMMIT
    # ========================================================

    def commit(
        self,
    ) -> None:

        self.db.commit()

    # ========================================================
    # TRANSACTION: ROLLBACK
    # ========================================================

    def rollback(
        self,
    ) -> None:

        self.db.rollback()

    # ========================================================
    # TRANSACTION: FLUSH
    # ========================================================

    def flush(
        self,
    ) -> None:

        self.db.flush()

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(
        self,
        activity: Activity,
    ) -> Activity:

        self.db.refresh(
            activity,
        )

        return activity