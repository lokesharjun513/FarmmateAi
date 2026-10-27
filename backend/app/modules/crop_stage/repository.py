from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.crop_stage.models import (
    CropStage,
    CropStageStatus,
)


class CropStageRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ============================================================
    # GET BY ID
    # ============================================================

    def get_by_id(
        self,
        stage_id: UUID,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.id == stage_id,
            )
            .first()
        )

    # ============================================================
    # GET BY ID FOR UPDATE
    #
    # Used during lifecycle transitions.
    #
    # Example:
    #
    # ACTIVE → COMPLETED
    #
    # The row is locked inside the current transaction.
    #
    # IMPORTANT:
    #
    # This only has an effect when the database transaction
    # remains open.
    #
    # ============================================================

    def get_by_id_for_update(
        self,
        stage_id: UUID,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.id == stage_id,
            )
            .with_for_update()
            .first()
        )

    # ============================================================
    # GET ALL STAGES
    #
    # Always ordered by stage_order.
    #
    # ============================================================

    def get_all_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> list[CropStage]:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .all()
        )

    # ============================================================
    # GET FIRST STAGE
    #
    # Returns first stage regardless of status.
    # ============================================================

    def get_first_stage(
        self,
        crop_season_id: UUID,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .first()
        )

    # ============================================================
    # GET LAST STAGE
    # ============================================================

    def get_last_stage(
        self,
        crop_season_id: UUID,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
            )
            .order_by(
                CropStage.stage_order.desc(),
                CropStage.created_at.desc(),
            )
            .first()
        )

    # ============================================================
    # GET ACTIVE STAGE
    #
    # Normally there should be only one ACTIVE stage.
    # ============================================================

    def get_active_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.ACTIVE,
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .first()
        )

    # ============================================================
    # GET ACTIVE STAGE FOR UPDATE
    #
    # Used during stage lifecycle transitions.
    #
    # ============================================================

    def get_active_by_crop_season_for_update(
        self,
        crop_season_id: UUID,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.ACTIVE,
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .with_for_update()
            .first()
        )

    # ============================================================
    # GET CURRENT STAGE
    #
    # Alias for the active stage.
    #
    # Useful for application/business terminology.
    # ============================================================

    def get_current_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> CropStage | None:

        return self.get_active_by_crop_season(
            crop_season_id,
        )

    # ============================================================
    # GET PENDING STAGES
    # ============================================================

    def get_pending_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> list[CropStage]:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.PENDING,
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .all()
        )

    # ============================================================
    # GET FIRST PENDING STAGE
    #
    # This is the first pending stage by sequence.
    #
    # ============================================================

    def get_first_pending_stage(
        self,
        crop_season_id: UUID,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.PENDING,
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .first()
        )

    # ============================================================
    # GET FIRST PENDING STAGE FOR UPDATE
    #
    # Used when activating the next stage.
    # ============================================================

    def get_first_pending_stage_for_update(
        self,
        crop_season_id: UUID,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.PENDING,
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .with_for_update()
            .first()
        )

    # ============================================================
    # GET NEXT PENDING STAGE
    #
    # Finds first pending stage after current stage.
    #
    # ============================================================

    def get_next_pending_stage(
        self,
        crop_season_id: UUID,
        current_stage_order: int,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.PENDING,
                CropStage.stage_order > current_stage_order,
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .first()
        )

    # ============================================================
    # GET NEXT STAGE
    #
    # Returns next stage regardless of status.
    # ============================================================

    def get_next_stage(
        self,
        crop_season_id: UUID,
        current_stage_order: int,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.stage_order > current_stage_order,
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .first()
        )

    # ============================================================
    # GET PREVIOUS STAGE
    #
    # Returns previous stage regardless of status.
    # ============================================================

    def get_previous_stage(
        self,
        crop_season_id: UUID,
        current_stage_order: int,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.stage_order < current_stage_order,
            )
            .order_by(
                CropStage.stage_order.desc(),
                CropStage.created_at.desc(),
            )
            .first()
        )

    # ============================================================
    # GET COMPLETED STAGES
    # ============================================================

    def get_completed_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> list[CropStage]:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.COMPLETED,
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .all()
        )

    # ============================================================
    # GET SKIPPED STAGES
    # ============================================================

    def get_skipped_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> list[CropStage]:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.SKIPPED,
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .all()
        )

    # ============================================================
    # GET FINISHED STAGES
    #
    # COMPLETED + SKIPPED
    # ============================================================

    def get_finished_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> list[CropStage]:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status.in_(
                    [
                        CropStageStatus.COMPLETED,
                        CropStageStatus.SKIPPED,
                    ]
                ),
            )
            .order_by(
                CropStage.stage_order.asc(),
                CropStage.created_at.asc(),
            )
            .all()
        )

    # ============================================================
    # CREATE
    #
    # Standalone transaction.
    # ============================================================

    def create(
        self,
        stage: CropStage,
    ) -> CropStage:

        self.db.add(stage)

        self.db.commit()

        self.db.refresh(stage)

        return stage

    # ============================================================
    # CREATE WITHOUT COMMIT
    #
    # Used inside larger transactions.
    # ============================================================

    def create_without_commit(
        self,
        stage: CropStage,
    ) -> CropStage:

        self.db.add(stage)

        self.db.flush()

        return stage

    # ============================================================
    # CREATE MANY
    #
    # Does NOT commit.
    #
    # Important for AI crop plan generation.
    # ============================================================

    def create_many(
        self,
        stages: list[CropStage],
    ) -> list[CropStage]:

        if not stages:
            return []

        self.db.add_all(stages)

        self.db.flush()

        return stages

    # ============================================================
    # CREATE MANY WITHOUT COMMIT
    #
    # Compatibility alias.
    # ============================================================

    def create_many_without_commit(
        self,
        stages: list[CropStage],
    ) -> list[CropStage]:

        return self.create_many(
            stages,
        )

    # ============================================================
    # UPDATE
    #
    # Standalone transaction.
    # ============================================================

    def update(
        self,
        stage: CropStage,
    ) -> CropStage:

        self.db.flush()

        self.db.commit()

        self.db.refresh(stage)

        return stage

    # ============================================================
    # UPDATE WITHOUT COMMIT
    # ============================================================

    def update_without_commit(
        self,
        stage: CropStage,
    ) -> CropStage:

        self.db.flush()

        return stage

    # ============================================================
    # DELETE
    #
    # Standalone transaction.
    # ============================================================

    def delete(
        self,
        stage: CropStage,
    ) -> None:

        self.db.delete(stage)

        self.db.commit()

    # ============================================================
    # DELETE WITHOUT COMMIT
    # ============================================================

    def delete_without_commit(
        self,
        stage: CropStage,
    ) -> None:

        self.db.delete(stage)

        self.db.flush()

    # ============================================================
    # DELETE ALL STAGES FOR CROP SEASON
    #
    # Does NOT commit.
    #
    # Used during AI plan regeneration.
    # ============================================================

    def delete_all_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> None:

        stages = (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
            )
            .all()
        )

        for stage in stages:
            self.db.delete(stage)

        self.db.flush()

    # ============================================================
    # COUNT ALL STAGES
    # ============================================================

    def count_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> int:

        return (
            self.db.query(CropStage.id)
            .filter(
                CropStage.crop_season_id == crop_season_id,
            )
            .count()
        )

    # ============================================================
    # COUNT PENDING
    # ============================================================

    def count_pending_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> int:

        return (
            self.db.query(CropStage.id)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.PENDING,
            )
            .count()
        )

    # ============================================================
    # COUNT ACTIVE
    # ============================================================

    def count_active_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> int:

        return (
            self.db.query(CropStage.id)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.ACTIVE,
            )
            .count()
        )

    # ============================================================
    # COUNT COMPLETED
    # ============================================================

    def count_completed_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> int:

        return (
            self.db.query(CropStage.id)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.COMPLETED,
            )
            .count()
        )

    # ============================================================
    # COUNT SKIPPED
    # ============================================================

    def count_skipped_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> int:

        return (
            self.db.query(CropStage.id)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.SKIPPED,
            )
            .count()
        )

    # ============================================================
    # COUNT FINISHED
    #
    # COMPLETED + SKIPPED
    # ============================================================

    def count_finished_by_crop_season(
        self,
        crop_season_id: UUID,
    ) -> int:

        return (
            self.db.query(CropStage.id)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status.in_(
                    [
                        CropStageStatus.COMPLETED,
                        CropStageStatus.SKIPPED,
                    ]
                ),
            )
            .count()
        )

    # ============================================================
    # COUNT BY STATUS
    #
    # Generic count helper.
    #
    # Useful for dashboards and analytics.
    # ============================================================

    def count_by_status(
        self,
        crop_season_id: UUID,
        status: CropStageStatus,
    ) -> int:

        return (
            self.db.query(CropStage.id)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == status,
            )
            .count()
        )

    # ============================================================
    # CHECK ACTIVE STAGE
    # ============================================================

    def has_active_stage(
        self,
        crop_season_id: UUID,
    ) -> bool:

        return (
            self.db.query(CropStage.id)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.ACTIVE,
            )
            .first()
            is not None
        )

    # ============================================================
    # CHECK PENDING STAGES
    # ============================================================

    def has_pending_stages(
        self,
        crop_season_id: UUID,
    ) -> bool:

        return (
            self.db.query(CropStage.id)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status == CropStageStatus.PENDING,
            )
            .first()
            is not None
        )

    # ============================================================
    # CHECK WHETHER ALL STAGES ARE FINISHED
    #
    # COMPLETED + SKIPPED = FINISHED
    #
    # PENDING + ACTIVE = UNFINISHED
    #
    # Zero stages:
    #
    #     True at repository level.
    #
    # The service decides whether zero stages should count
    # as a completed crop.
    # ============================================================

    def all_finished(
        self,
        crop_season_id: UUID,
    ) -> bool:

        unfinished_count = (
            self.db.query(CropStage.id)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.status.in_(
                    [
                        CropStageStatus.PENDING,
                        CropStageStatus.ACTIVE,
                    ]
                ),
            )
            .count()
        )

        return unfinished_count == 0

    # ============================================================
    # BACKWARD-COMPATIBILITY ALIAS
    # ============================================================

    def all_completed(
        self,
        crop_season_id: UUID,
    ) -> bool:

        return self.all_finished(
            crop_season_id,
        )

    # ============================================================
    # CHECK WHETHER STAGE EXISTS
    # ============================================================

    def exists(
        self,
        stage_id: UUID,
    ) -> bool:

        return (
            self.db.query(CropStage.id)
            .filter(
                CropStage.id == stage_id,
            )
            .first()
            is not None
        )

    # ============================================================
    # CHECK STAGE EXISTS IN CROP SEASON
    # ============================================================

    def exists_by_crop_season(
        self,
        stage_id: UUID,
        crop_season_id: UUID,
    ) -> bool:

        return (
            self.db.query(CropStage.id)
            .filter(
                CropStage.id == stage_id,
                CropStage.crop_season_id == crop_season_id,
            )
            .first()
            is not None
        )

    # ============================================================
    # GET STAGE BY ORDER
    # ============================================================

    def get_by_stage_order(
        self,
        crop_season_id: UUID,
        stage_order: int,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.stage_order == stage_order,
            )
            .first()
        )

    # ============================================================
    # GET STAGE BY ORDER AND STATUS
    # ============================================================

    def get_by_stage_order_and_status(
        self,
        crop_season_id: UUID,
        stage_order: int,
        status: CropStageStatus,
    ) -> CropStage | None:

        return (
            self.db.query(CropStage)
            .filter(
                CropStage.crop_season_id == crop_season_id,
                CropStage.stage_order == stage_order,
                CropStage.status == status,
            )
            .first()
        )

    # ============================================================
    # COMMIT
    # ============================================================

    def commit(
        self,
    ) -> None:

        self.db.commit()

    # ============================================================
    # ROLLBACK
    # ============================================================

    def rollback(
        self,
    ) -> None:

        self.db.rollback()

    # ============================================================
    # FLUSH
    # ============================================================

    def flush(
        self,
    ) -> None:

        self.db.flush()

    # ============================================================
    # REFRESH
    # ============================================================

    def refresh(
        self,
        stage: CropStage,
    ) -> CropStage:

        self.db.refresh(stage)

        return stage