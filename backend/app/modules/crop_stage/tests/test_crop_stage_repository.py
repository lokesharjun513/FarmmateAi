from datetime import date
from uuid import uuid4

import pytest

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
    FarmingSeason,
)

from app.modules.crop_stage.models import (
    CropStage,
    CropStageStatus,
)

from app.modules.crop_stage.repository import (
    CropStageRepository,
)


# ============================================================
# HELPERS
# ============================================================


def create_crop_season(
    db,
    *,
    status=CropSeasonStatus.PLANNED,
):
    crop_season = CropSeason(
        farm_id=uuid4(),
        crop_name="Rice",
        crop_variety="BPT",
        land_area=1.0,
        land_unit="Acres",
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date.today(),
        expected_harvest_date=None,
        harvested_date=None,
        status=status,
        is_active=(
            status == CropSeasonStatus.ACTIVE
        ),
        notes=None,
    )

    db.add(crop_season)
    db.commit()
    db.refresh(crop_season)

    return crop_season


def create_stage(
    db,
    crop_season,
    *,
    order=1,
    status=CropStageStatus.PENDING,
):
    stage = CropStage(
        crop_season_id=crop_season.id,
        name=f"Stage {order}",
        description=f"Description {order}",
        stage_order=order,
        start_day=order,
        end_day=order + 5,
        status=status,
        started_at=(
            date.today()
            if status
            in (
                CropStageStatus.ACTIVE,
                CropStageStatus.COMPLETED,
                CropStageStatus.SKIPPED,
            )
            else None
        ),
        completed_at=(
            date.today()
            if status
            in (
                CropStageStatus.COMPLETED,
                CropStageStatus.SKIPPED,
            )
            else None
        ),
    )

    db.add(stage)
    db.commit()
    db.refresh(stage)

    return stage


# ============================================================
# GET BY ID
# ============================================================


def test_get_by_id(db):

    crop_season = create_crop_season(db)

    stage = create_stage(
        db,
        crop_season,
    )

    repository = CropStageRepository(db)

    result = repository.get_by_id(stage.id)

    assert result is not None
    assert result.id == stage.id


def test_get_by_id_not_found(db):

    repository = CropStageRepository(db)

    result = repository.get_by_id(uuid4())

    assert result is None


# ============================================================
# GET ALL
# ============================================================


def test_get_all_by_crop_season_is_ordered(db):

    crop_season = create_crop_season(db)

    create_stage(
        db,
        crop_season,
        order=1,
    )

    create_stage(
        db,
        crop_season,
        order=2,
    )

    create_stage(
        db,
        crop_season,
        order=3,
    )

    repository = CropStageRepository(db)

    result = repository.get_all_by_crop_season(
        crop_season.id,
    )

    assert len(result) == 3
    assert [stage.stage_order for stage in result] == [
        1,
        2,
        3,
    ]


# ============================================================
# FIRST / LAST
# ============================================================


def test_get_first_stage(db):

    crop_season = create_crop_season(db)

    create_stage(db, crop_season, order=1)
    create_stage(db, crop_season, order=2)

    repository = CropStageRepository(db)

    result = repository.get_first_stage(
        crop_season.id,
    )

    assert result.stage_order == 1


def test_get_last_stage(db):

    crop_season = create_crop_season(db)

    create_stage(db, crop_season, order=1)
    create_stage(db, crop_season, order=2)

    repository = CropStageRepository(db)

    result = repository.get_last_stage(
        crop_season.id,
    )

    assert result.stage_order == 2


# ============================================================
# STATUS QUERIES
# ============================================================


def test_get_active_stage(db):

    crop_season = create_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    create_stage(
        db,
        crop_season,
        status=CropStageStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    result = repository.get_active_by_crop_season(
        crop_season.id,
    )

    assert result is not None
    assert result.status == CropStageStatus.ACTIVE


def test_get_pending_stages(db):

    crop_season = create_crop_season(db)

    create_stage(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.PENDING,
    )

    create_stage(
        db,
        crop_season,
        order=2,
        status=CropStageStatus.COMPLETED,
    )

    repository = CropStageRepository(db)

    result = repository.get_pending_by_crop_season(
        crop_season.id,
    )

    assert len(result) == 1
    assert result[0].stage_order == 1


def test_get_completed_stages(db):

    crop_season = create_crop_season(db)

    create_stage(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.COMPLETED,
    )

    repository = CropStageRepository(db)

    result = repository.get_completed_by_crop_season(
        crop_season.id,
    )

    assert len(result) == 1
    assert result[0].status == CropStageStatus.COMPLETED


def test_get_skipped_stages(db):

    crop_season = create_crop_season(db)

    create_stage(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.SKIPPED,
    )

    repository = CropStageRepository(db)

    result = repository.get_skipped_by_crop_season(
        crop_season.id,
    )

    assert len(result) == 1
    assert result[0].status == CropStageStatus.SKIPPED


def test_get_finished_stages_includes_completed_and_skipped(
    db,
):

    crop_season = create_crop_season(db)

    create_stage(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.COMPLETED,
    )

    create_stage(
        db,
        crop_season,
        order=2,
        status=CropStageStatus.SKIPPED,
    )

    repository = CropStageRepository(db)

    result = repository.get_finished_by_crop_season(
        crop_season.id,
    )

    assert len(result) == 2


# ============================================================
# NEXT / PREVIOUS
# ============================================================


def test_get_next_stage(db):

    crop_season = create_crop_season(db)

    create_stage(db, crop_season, order=1)
    create_stage(db, crop_season, order=2)
    create_stage(db, crop_season, order=3)

    repository = CropStageRepository(db)

    result = repository.get_next_stage(
        crop_season.id,
        1,
    )

    assert result.stage_order == 2


def test_get_previous_stage(db):

    crop_season = create_crop_season(db)

    create_stage(db, crop_season, order=1)
    create_stage(db, crop_season, order=2)
    create_stage(db, crop_season, order=3)

    repository = CropStageRepository(db)

    result = repository.get_previous_stage(
        crop_season.id,
        3,
    )

    assert result.stage_order == 2


# ============================================================
# COUNTS
# ============================================================


def test_count_by_crop_season(db):

    crop_season = create_crop_season(db)

    create_stage(db, crop_season, order=1)
    create_stage(db, crop_season, order=2)

    repository = CropStageRepository(db)

    assert (
        repository.count_by_crop_season(
            crop_season.id,
        )
        == 2
    )


def test_count_statuses(db):

    crop_season = create_crop_season(db)

    create_stage(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.COMPLETED,
    )

    create_stage(
        db,
        crop_season,
        order=2,
        status=CropStageStatus.SKIPPED,
    )

    create_stage(
        db,
        crop_season,
        order=3,
        status=CropStageStatus.PENDING,
    )

    repository = CropStageRepository(db)

    assert repository.count_completed_by_crop_season(
        crop_season.id,
    ) == 1

    assert repository.count_skipped_by_crop_season(
        crop_season.id,
    ) == 1

    assert repository.count_pending_by_crop_season(
        crop_season.id,
    ) == 1

    assert repository.count_finished_by_crop_season(
        crop_season.id,
    ) == 2


# ============================================================
# EXISTS
# ============================================================


def test_exists(db):

    crop_season = create_crop_season(db)

    stage = create_stage(
        db,
        crop_season,
    )

    repository = CropStageRepository(db)

    assert repository.exists(stage.id) is True
    assert repository.exists(uuid4()) is False


def test_exists_by_crop_season(db):

    crop_season = create_crop_season(db)

    stage = create_stage(
        db,
        crop_season,
    )

    repository = CropStageRepository(db)

    assert repository.exists_by_crop_season(
        stage.id,
        crop_season.id,
    ) is True


# ============================================================
# ALL FINISHED
# ============================================================


def test_all_finished_returns_false_when_pending_exists(
    db,
):

    crop_season = create_crop_season(db)

    create_stage(
        db,
        crop_season,
        status=CropStageStatus.PENDING,
    )

    repository = CropStageRepository(db)

    assert repository.all_finished(
        crop_season.id,
    ) is False


def test_all_finished_returns_true_when_completed_and_skipped(
    db,
):

    crop_season = create_crop_season(db)

    create_stage(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.COMPLETED,
    )

    create_stage(
        db,
        crop_season,
        order=2,
        status=CropStageStatus.SKIPPED,
    )

    repository = CropStageRepository(db)

    assert repository.all_finished(
        crop_season.id,
    ) is True


def test_all_finished_with_zero_stages_repository_level(
    db,
):

    crop_season = create_crop_season(db)

    repository = CropStageRepository(db)

    assert repository.all_finished(
        crop_season.id,
    ) is True