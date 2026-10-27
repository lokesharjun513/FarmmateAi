from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
)

from app.modules.farm.models import Farm


class CropSeasonRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ============================================================
    # LOCK FARM ACTIVE-CROP SCOPE
    #
    # Serializes crop activation for the same farm.
    # ============================================================

    def lock_farm(
        self,
        farm_id: UUID,
    ) -> None:

        (
            self.db.query(Farm.id)
            .filter(
                Farm.id == farm_id,
            )
            .with_for_update()
            .first()
        )

    # ============================================================
    # GET BY ID
    # ============================================================

    def get_by_id(
        self,
        crop_season_id: UUID,
    ) -> CropSeason | None:

        return (
            self.db.query(CropSeason)
            .filter(
                CropSeason.id == crop_season_id,
            )
            .first()
        )

    # ============================================================
    # GET BY FARM AND ID
    # ============================================================

    def get_by_farm_and_id(
        self,
        farm_id: UUID,
        crop_season_id: UUID,
    ) -> CropSeason | None:

        return (
            self.db.query(CropSeason)
            .filter(
                CropSeason.id == crop_season_id,
                CropSeason.farm_id == farm_id,
            )
            .first()
        )

    # ============================================================
    # GET BY FARM AND STATUS
    # ============================================================

    def get_by_farm_and_status(
        self,
        farm_id: UUID,
        status: CropSeasonStatus,
    ) -> list[CropSeason]:

        return (
            self.db.query(CropSeason)
            .filter(
                CropSeason.farm_id == farm_id,
                CropSeason.status == status,
            )
            .order_by(
                CropSeason.created_at.desc(),
            )
            .all()
        )

    # ============================================================
    # GET ALL BY FARM
    # ============================================================

    def get_all_by_farm(
        self,
        farm_id: UUID,
    ) -> list[CropSeason]:

        return (
            self.db.query(CropSeason)
            .filter(
                CropSeason.farm_id == farm_id,
            )
            .order_by(
                CropSeason.created_at.desc(),
            )
            .all()
        )

    # ============================================================
    # GET ACTIVE CROP
    #
    # ACTIVE + is_active=True
    # ============================================================

    def get_active_by_farm(
        self,
        farm_id: UUID,
    ) -> CropSeason | None:

        return (
            self.db.query(CropSeason)
            .filter(
                CropSeason.farm_id == farm_id,
                CropSeason.status == CropSeasonStatus.ACTIVE,
                CropSeason.is_active.is_(True),
            )
            .order_by(
                CropSeason.created_at.desc(),
            )
            .first()
        )

    # ============================================================
    # GET ALL ACTIVE CROPS FOR FARM
    # ============================================================

    def get_all_active_by_farm(
        self,
        farm_id: UUID,
    ) -> list[CropSeason]:

        return (
            self.db.query(CropSeason)
            .filter(
                CropSeason.farm_id == farm_id,
                CropSeason.status == CropSeasonStatus.ACTIVE,
                CropSeason.is_active.is_(True),
            )
            .order_by(
                CropSeason.created_at.desc(),
            )
            .all()
        )

    # ============================================================
    # GET ALL ACTIVE CROPS
    #
    # Useful for:
    #
    # - Weather scheduler
    # - AI monitoring
    # - Notifications
    # - Background jobs
    # ============================================================

    def get_all_active(
        self,
    ) -> list[CropSeason]:

        return (
            self.db.query(CropSeason)
            .filter(
                CropSeason.status == CropSeasonStatus.ACTIVE,
                CropSeason.is_active.is_(True),
            )
            .order_by(
                CropSeason.created_at.desc(),
            )
            .all()
        )

    # ============================================================
    # GET ALL ACTIVE CROPS WITH FARM
    # ============================================================

    def get_all_active_with_farm(
        self,
    ) -> list[CropSeason]:

        return (
            self.db.query(CropSeason)
            .join(
                CropSeason.farm,
            )
            .filter(
                CropSeason.status == CropSeasonStatus.ACTIVE,
                CropSeason.is_active.is_(True),
            )
            .order_by(
                CropSeason.created_at.desc(),
            )
            .all()
        )

    # ============================================================
    # GET PLANNED CROPS
    # ============================================================

    def get_all_planned_by_farm(
        self,
        farm_id: UUID,
    ) -> list[CropSeason]:

        return self.get_by_farm_and_status(
            farm_id=farm_id,
            status=CropSeasonStatus.PLANNED,
        )

    # ============================================================
    # GET HARVESTED CROPS
    # ============================================================

    def get_all_harvested_by_farm(
        self,
        farm_id: UUID,
    ) -> list[CropSeason]:

        return self.get_by_farm_and_status(
            farm_id=farm_id,
            status=CropSeasonStatus.HARVESTED,
        )

    # ============================================================
    # GET CANCELLED CROPS
    # ============================================================

    def get_all_cancelled_by_farm(
        self,
        farm_id: UUID,
    ) -> list[CropSeason]:

        return self.get_by_farm_and_status(
            farm_id=farm_id,
            status=CropSeasonStatus.CANCELLED,
        )

    # ============================================================
    # GET LATEST CROP
    # ============================================================

    def get_latest_by_farm(
        self,
        farm_id: UUID,
    ) -> CropSeason | None:

        return (
            self.db.query(CropSeason)
            .filter(
                CropSeason.farm_id == farm_id,
            )
            .order_by(
                CropSeason.created_at.desc(),
            )
            .first()
        )

    # ============================================================
    # GET BY FARM AND CROP NAME
    # ============================================================

    def get_by_farm_and_crop(
        self,
        farm_id: UUID,
        crop_name: str,
    ) -> CropSeason | None:

        return (
            self.db.query(CropSeason)
            .filter(
                CropSeason.farm_id == farm_id,
                CropSeason.crop_name == crop_name,
            )
            .order_by(
                CropSeason.created_at.desc(),
            )
            .first()
        )

    # ============================================================
    # CREATE
    #
    # Standalone transaction.
    # ============================================================

    def create(
        self,
        crop_season: CropSeason,
    ) -> CropSeason:

        self.db.add(
            crop_season,
        )

        self.db.commit()

        self.db.refresh(
            crop_season,
        )

        return crop_season

    # ============================================================
    # CREATE WITHOUT COMMIT
    # ============================================================

    def create_without_commit(
        self,
        crop_season: CropSeason,
    ) -> CropSeason:

        self.db.add(
            crop_season,
        )

        self.db.flush()

        return crop_season

    # ============================================================
    # UPDATE
    #
    # Standalone transaction.
    # ============================================================

    def update(
        self,
        crop_season: CropSeason,
    ) -> CropSeason:

        self.db.flush()

        self.db.commit()

        self.db.refresh(
            crop_season,
        )

        return crop_season

    # ============================================================
    # UPDATE WITHOUT COMMIT
    # ============================================================

    def update_without_commit(
        self,
        crop_season: CropSeason,
    ) -> CropSeason:

        self.db.flush()

        return crop_season

    # ============================================================
    # DELETE
    # ============================================================

    def delete(
        self,
        crop_season: CropSeason,
    ) -> None:

        self.db.delete(
            crop_season,
        )

        self.db.commit()

    # ============================================================
    # DELETE WITHOUT COMMIT
    # ============================================================

    def delete_without_commit(
        self,
        crop_season: CropSeason,
    ) -> None:

        self.db.delete(
            crop_season,
        )

        self.db.flush()

    # ============================================================
    # MARK ACTIVE
    #
    # PLANNED
    #    ↓
    # ACTIVE
    #
    # is_active = True
    #
    # ============================================================

    def mark_active(
        self,
        crop_season: CropSeason,
    ) -> CropSeason:

        crop_season.status = (
            CropSeasonStatus.ACTIVE
        )

        crop_season.is_active = True

        self.db.flush()

        return crop_season

    # ============================================================
    # MARK HARVESTED
    #
    # ACTIVE
    #    ↓
    # HARVESTED
    #
    # is_active = False
    #
    # harvested_date is assigned by the service.
    #
    # ============================================================

    def mark_harvested(
        self,
        crop_season: CropSeason,
    ) -> CropSeason:

        crop_season.status = (
            CropSeasonStatus.HARVESTED
        )

        crop_season.is_active = False

        self.db.flush()

        return crop_season

    # ============================================================
    # MARK CANCELLED
    #
    # PLANNED / ACTIVE
    #       ↓
    # CANCELLED
    #
    # ============================================================

    def mark_cancelled(
        self,
        crop_season: CropSeason,
    ) -> CropSeason:

        crop_season.status = (
            CropSeasonStatus.CANCELLED
        )

        crop_season.is_active = False

        self.db.flush()

        return crop_season

    # ============================================================
    # CHECK ACTIVE CROP
    # ============================================================

    def has_active_crop(
        self,
        farm_id: UUID,
    ) -> bool:

        return (
            self.db.query(CropSeason.id)
            .filter(
                CropSeason.farm_id == farm_id,
                CropSeason.status == CropSeasonStatus.ACTIVE,
                CropSeason.is_active.is_(True),
            )
            .first()
            is not None
        )

    # ============================================================
    # CHECK PLANNED CROP
    # ============================================================

    def has_planned_crop(
        self,
        farm_id: UUID,
    ) -> bool:

        return (
            self.db.query(CropSeason.id)
            .filter(
                CropSeason.farm_id == farm_id,
                CropSeason.status == CropSeasonStatus.PLANNED,
            )
            .first()
            is not None
        )

    # ============================================================
    # CHECK STATUS
    # ============================================================

    def exists_by_status(
        self,
        farm_id: UUID,
        status: CropSeasonStatus,
    ) -> bool:

        return (
            self.db.query(CropSeason.id)
            .filter(
                CropSeason.farm_id == farm_id,
                CropSeason.status == status,
            )
            .first()
            is not None
        )

    # ============================================================
    # EXISTS
    # ============================================================

    def exists(
        self,
        crop_season_id: UUID,
    ) -> bool:

        return (
            self.db.query(CropSeason.id)
            .filter(
                CropSeason.id == crop_season_id,
            )
            .first()
            is not None
        )

    # ============================================================
    # COUNTS
    # ============================================================

    def count_by_farm(
        self,
        farm_id: UUID,
    ) -> int:

        return (
            self.db.query(CropSeason.id)
            .filter(
                CropSeason.farm_id == farm_id,
            )
            .count()
        )

    # ============================================================
    # COUNT ACTIVE
    # ============================================================

    def count_active_by_farm(
        self,
        farm_id: UUID,
    ) -> int:

        return (
            self.db.query(CropSeason.id)
            .filter(
                CropSeason.farm_id == farm_id,
                CropSeason.status == CropSeasonStatus.ACTIVE,
                CropSeason.is_active.is_(True),
            )
            .count()
        )

    # ============================================================
    # COUNT PLANNED
    # ============================================================

    def count_planned_by_farm(
        self,
        farm_id: UUID,
    ) -> int:

        return (
            self.db.query(CropSeason.id)
            .filter(
                CropSeason.farm_id == farm_id,
                CropSeason.status == CropSeasonStatus.PLANNED,
            )
            .count()
        )

    # ============================================================
    # COUNT HARVESTED
    # ============================================================

    def count_harvested_by_farm(
        self,
        farm_id: UUID,
    ) -> int:

        return (
            self.db.query(CropSeason.id)
            .filter(
                CropSeason.farm_id == farm_id,
                CropSeason.status == CropSeasonStatus.HARVESTED,
            )
            .count()
        )

    # ============================================================
    # COUNT CANCELLED
    # ============================================================

    def count_cancelled_by_farm(
        self,
        farm_id: UUID,
    ) -> int:

        return (
            self.db.query(CropSeason.id)
            .filter(
                CropSeason.farm_id == farm_id,
                CropSeason.status == CropSeasonStatus.CANCELLED,
            )
            .count()
        )

    # ============================================================
    # TRANSACTION: COMMIT
    # ============================================================

    def commit(
        self,
    ) -> None:

        self.db.commit()

    # ============================================================
    # TRANSACTION: ROLLBACK
    # ============================================================

    def rollback(
        self,
    ) -> None:

        self.db.rollback()

    # ============================================================
    # TRANSACTION: FLUSH
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
        crop_season: CropSeason,
    ) -> CropSeason:

        self.db.refresh(
            crop_season,
        )

        return crop_season