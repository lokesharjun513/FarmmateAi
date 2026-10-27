from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.activity.models import Activity
from app.modules.crop_season.models import CropSeason
from app.modules.crop_stage.models import CropStage


class CropPlannerRepository:

    def __init__(
        self,
        db: Session,
    ):

        self.db = db

    # ========================================================
    # LOCK CROP SEASON
    #
    # Serializes plan persistence for the same crop season.
    # ========================================================

    def lock_crop_season(
        self,
        crop_season_id: UUID,
    ) -> CropSeason | None:

        return (
            self.db.query(CropSeason)
            .filter(
                CropSeason.id == crop_season_id,
            )
            .with_for_update()
            .first()
        )

    # ========================================================
    # CHECK WHETHER PLAN EXISTS
    # ========================================================

    def has_plan(
        self,
        crop_season_id: UUID,
    ) -> bool:

        return (
            self.db.query(
                CropStage.id,
            )
            .filter(
                CropStage.crop_season_id
                == crop_season_id,
            )
            .first()
            is not None
        )

    # ========================================================
    # CREATE STAGE
    # ========================================================

    def create_stage(
        self,
        stage: CropStage,
    ) -> CropStage:

        self.db.add(
            stage,
        )

        self.db.flush()

        return stage

    # ========================================================
    # CREATE ACTIVITIES
    # ========================================================

    def create_activities(
        self,
        activities: list[Activity],
    ) -> list[Activity]:

        if not activities:
            return []

        self.db.add_all(
            activities,
        )

        self.db.flush()

        return activities

    # ========================================================
    # COMMIT
    # ========================================================

    def commit(
        self,
    ) -> None:

        self.db.commit()

    # ========================================================
    # ROLLBACK
    # ========================================================

    def rollback(
        self,
    ) -> None:

        self.db.rollback()

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(
        self,
        instance,
    ):

        self.db.refresh(
            instance,
        )

        return instance