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

from app.modules.crop_stage.schemas import (
    CropStageCreateRequest,
    CropStageUpdateRequest,
)

from app.modules.crop_stage.service import (
    activate_first_stage,
    activate_next_stage,
    activate_stage,
    all_stages_completed,
    complete_stage,
    create_stage,
    delete_all_stages,
    delete_stage,
    get_active_stage,
    get_crop_stages,
    get_next_stage,
    get_pending_stages,
    skip_stage,
    update_stage,
)

from app.shared.exceptions import (
    ValidationError,
)


# ============================================================
# HELPERS
# ============================================================


def create_test_crop_season(
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


def create_stage_direct(
    db,
    crop_season,
    *,
    order,
    status=CropStageStatus.PENDING,
):

    stage = CropStage(
        crop_season_id=crop_season.id,
        name=f"Stage {order}",
        description=f"Stage {order} description",
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


def create_stage_request(
    *,
    order=1,
):

    return CropStageCreateRequest(
        name=f"Stage {order}",
        description=f"Description {order}",
        stage_order=order,
        start_day=order,
        end_day=order + 5,
    )


# ============================================================
# CREATE
# ============================================================


def test_create_stage(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.PLANNED,
    )

    repository = CropStageRepository(db)

    result = create_stage(
        repository,
        crop_season.id,
        create_stage_request(order=1),
    )

    assert result.crop_season_id == crop_season.id
    assert result.name == "Stage 1"
    assert result.stage_order == 1
    assert result.status == CropStageStatus.PENDING
    assert result.started_at is None
    assert result.completed_at is None


def test_create_stage_requires_planned_crop(
    db,
):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    with pytest.raises(
        ValidationError,
        match="Crop stages can only be created before farming starts",
    ):
        create_stage(
            repository,
            crop_season.id,
            create_stage_request(order=1),
        )


def test_create_stage_crop_not_found(db):

    repository = CropStageRepository(db)

    with pytest.raises(
        ValidationError,
        match="Crop season not found",
    ):
        create_stage(
            repository,
            uuid4(),
            create_stage_request(order=1),
        )


def test_create_stage_must_start_at_order_one(
    db,
):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    with pytest.raises(
        ValidationError,
        match="Next crop stage must have stage order 1",
    ):
        create_stage(
            repository,
            crop_season.id,
            create_stage_request(order=2),
        )


def test_create_stage_must_be_sequential(db):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    create_stage(
        repository,
        crop_season.id,
        create_stage_request(order=1),
    )

    with pytest.raises(
        ValidationError,
        match="Next crop stage must have stage order 2",
    ):
        create_stage(
            repository,
            crop_season.id,
            create_stage_request(order=3),
        )


def test_create_multiple_stages_in_sequence(db):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    stage1 = create_stage(
        repository,
        crop_season.id,
        create_stage_request(order=1),
    )

    stage2 = create_stage(
        repository,
        crop_season.id,
        create_stage_request(order=2),
    )

    assert stage1.stage_order == 1
    assert stage2.stage_order == 2


# ============================================================
# GET
# ============================================================


def test_get_crop_stages(db):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    create_stage(
        repository,
        crop_season.id,
        create_stage_request(order=1),
    )

    create_stage(
        repository,
        crop_season.id,
        create_stage_request(order=2),
    )

    result = get_crop_stages(
        repository,
        crop_season.id,
    )

    assert len(result) == 2
    assert [stage.stage_order for stage in result] == [
        1,
        2,
    ]


def test_get_pending_stages(db):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.PENDING,
    )

    result = get_pending_stages(
        repository,
        crop_season.id,
    )

    assert len(result) == 1


def test_get_active_stage(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.ACTIVE,
    )

    result = get_active_stage(
        repository,
        crop_season.id,
    )

    assert result is not None
    assert result.status == CropStageStatus.ACTIVE


# ============================================================
# ACTIVATE FIRST STAGE
# ============================================================


def test_activate_first_stage(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    result = activate_first_stage(
        repository,
        crop_season.id,
    )

    assert result.id == stage.id
    assert result.status == CropStageStatus.ACTIVE
    assert result.started_at == crop_season.sowing_date
    assert result.completed_at is None


def test_activate_first_stage_requires_active_crop(
    db,
):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.PLANNED,
    )

    repository = CropStageRepository(db)

    create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    with pytest.raises(
        ValidationError,
        match="Crop farming must be active before activating a stage",
    ):
        activate_first_stage(
            repository,
            crop_season.id,
        )


def test_activate_first_stage_requires_order_one(
    db,
):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    # Bypass service to deliberately create invalid plan.
    create_stage_direct(
        db,
        crop_season,
        order=2,
    )

    with pytest.raises(
        ValidationError,
        match="Crop plan must start with stage order 1",
    ):
        activate_first_stage(
            repository,
            crop_season.id,
        )


# ============================================================
# ACTIVATE STAGE
# ============================================================


def test_activate_stage(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    result = activate_stage(
        repository,
        stage,
    )

    assert result.status == CropStageStatus.ACTIVE
    assert result.started_at == date.today()
    assert result.completed_at is None


def test_activate_stage_is_idempotent(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.ACTIVE,
    )

    result = activate_stage(
        repository,
        stage,
    )

    assert result.status == CropStageStatus.ACTIVE


def test_completed_stage_cannot_activate(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.COMPLETED,
    )

    with pytest.raises(
        ValidationError,
        match="Completed crop stage cannot be activated again",
    ):
        activate_stage(
            repository,
            stage,
        )


def test_skipped_stage_cannot_activate(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.SKIPPED,
    )

    with pytest.raises(
        ValidationError,
        match="Skipped crop stage cannot be activated again",
    ):
        activate_stage(
            repository,
            stage,
        )


def test_cannot_activate_second_stage_before_first(
    db,
):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    stage2 = create_stage_direct(
        db,
        crop_season,
        order=2,
    )

    with pytest.raises(
        ValidationError,
        match="Stages must be completed in order",
    ):
        activate_stage(
            repository,
            stage2,
        )


def test_only_one_stage_can_be_active(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage1 = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.ACTIVE,
    )

    stage2 = create_stage_direct(
        db,
        crop_season,
        order=2,
    )

    with pytest.raises(
        ValidationError,
        match="Another crop stage is already active",
    ):
        activate_stage(
            repository,
            stage2,
        )


# ============================================================
# COMPLETE
# ============================================================


def test_complete_stage(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage1 = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.ACTIVE,
    )

    create_stage_direct(
        db,
        crop_season,
        order=2,
    )

    result = complete_stage(
        repository,
        stage1,
    )

    assert result.status == CropStageStatus.COMPLETED
    assert result.completed_at == date.today()


def test_complete_stage_automatically_activates_next(
    db,
):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage1 = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.ACTIVE,
    )

    stage2 = create_stage_direct(
        db,
        crop_season,
        order=2,
    )

    complete_stage(
        repository,
        stage1,
    )

    db.refresh(stage2)

    assert stage1.status == CropStageStatus.COMPLETED
    assert stage1.completed_at == date.today()

    assert stage2.status == CropStageStatus.ACTIVE
    assert stage2.started_at == date.today()


def test_pending_stage_cannot_complete(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    with pytest.raises(
        ValidationError,
        match="Only an active crop stage can be completed",
    ):
        complete_stage(
            repository,
            stage,
        )


def test_completed_stage_cannot_complete_again(
    db,
):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.COMPLETED,
    )

    with pytest.raises(
        ValidationError,
        match="Only an active crop stage can be completed",
    ):
        complete_stage(
            repository,
            stage,
        )


# ============================================================
# SKIP
# ============================================================


def test_skip_stage(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.ACTIVE,
    )

    result = skip_stage(
        repository,
        stage,
    )

    assert result.status == CropStageStatus.SKIPPED
    assert result.completed_at == date.today()


def test_skip_stage_automatically_activates_next(
    db,
):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage1 = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.ACTIVE,
    )

    stage2 = create_stage_direct(
        db,
        crop_season,
        order=2,
    )

    skip_stage(
        repository,
        stage1,
    )

    db.refresh(stage2)

    assert stage1.status == CropStageStatus.SKIPPED
    assert stage1.completed_at == date.today()

    assert stage2.status == CropStageStatus.ACTIVE


def test_pending_stage_cannot_skip(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    with pytest.raises(
        ValidationError,
        match="Only the active crop stage can be skipped",
    ):
        skip_stage(
            repository,
            stage,
        )


def test_completed_stage_cannot_skip(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.COMPLETED,
    )

    with pytest.raises(
        ValidationError,
        match="Completed crop stage cannot be skipped",
    ):
        skip_stage(
            repository,
            stage,
        )


def test_skip_stage_is_idempotent(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.SKIPPED,
    )

    result = skip_stage(
        repository,
        stage,
    )

    assert result.status == CropStageStatus.SKIPPED


# ============================================================
# ACTIVATE NEXT
# ============================================================


def test_activate_next_stage(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage1 = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.COMPLETED,
    )

    stage2 = create_stage_direct(
        db,
        crop_season,
        order=2,
    )

    result = activate_next_stage(
        repository,
        stage1,
    )

    assert result is not None
    assert result.id == stage2.id
    assert result.status == CropStageStatus.ACTIVE


def test_activate_next_requires_finished_current_stage(
    db,
):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage1 = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.ACTIVE,
    )

    with pytest.raises(
        ValidationError,
        match="Current stage must be completed or skipped",
    ):
        activate_next_stage(
            repository,
            stage1,
        )


def test_activate_next_returns_none_for_final_stage(
    db,
):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage1 = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.COMPLETED,
    )

    result = activate_next_stage(
        repository,
        stage1,
    )

    assert result is None


# ============================================================
# UPDATE
# ============================================================


def test_update_pending_stage(db):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    request = CropStageUpdateRequest(
        name="Updated Stage",
        description="Updated description",
        start_day=5,
        end_day=15,
    )

    result = update_stage(
        repository,
        stage,
        request,
    )

    assert result.name == "Updated Stage"
    assert result.description == "Updated description"
    assert result.start_day == 5
    assert result.end_day == 15
    assert result.stage_order == 1
    assert result.status == CropStageStatus.PENDING


def test_update_empty_request_does_nothing(db):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    original_name = stage.name

    result = update_stage(
        repository,
        stage,
        CropStageUpdateRequest(),
    )

    assert result.name == original_name


def test_update_stage_order_cannot_change(db):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    request = CropStageUpdateRequest(
        stage_order=2,
    )

    with pytest.raises(
        ValidationError,
        match="Stage order cannot be changed",
    ):
        update_stage(
            repository,
            stage,
            request,
        )


def test_update_completed_stage_not_allowed(
    db,
):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.COMPLETED,
    )

    request = CropStageUpdateRequest(
        name="Updated",
    )

    with pytest.raises(
        ValidationError,
        match="Only pending crop stages can be edited",
    ):
        update_stage(
            repository,
            stage,
            request,
        )


def test_update_active_crop_not_allowed(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    request = CropStageUpdateRequest(
        name="Updated",
    )

    with pytest.raises(
        ValidationError,
        match="Crop stages can only be edited before farming starts",
    ):
        update_stage(
            repository,
            stage,
            request,
        )


# ============================================================
# DELETE
# ============================================================


def test_delete_last_pending_stage(db):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    stage1 = create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    stage2 = create_stage_direct(
        db,
        crop_season,
        order=2,
    )

    delete_stage(
        repository,
        stage2,
    )

    assert repository.get_by_id(stage2.id) is None
    assert repository.get_by_id(stage1.id) is not None


def test_only_last_stage_can_be_deleted(db):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    stage1 = create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    create_stage_direct(
        db,
        crop_season,
        order=2,
    )

    with pytest.raises(
        ValidationError,
        match="Only the last crop stage can be deleted",
    ):
        delete_stage(
            repository,
            stage1,
        )


def test_active_stage_cannot_be_deleted(db):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    stage = create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.ACTIVE,
    )

    with pytest.raises(
        ValidationError,
        match="Crop stages cannot be deleted after farming starts",
    ):
        delete_stage(
            repository,
            stage,
        )


# ============================================================
# DELETE ALL
# ============================================================


def test_delete_all_stages(db):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    create_stage_direct(
        db,
        crop_season,
        order=2,
    )

    delete_all_stages(
        repository,
        crop_season.id,
    )

    assert repository.count_by_crop_season(
        crop_season.id,
    ) == 0


def test_delete_all_stages_requires_planned_crop(
    db,
):

    crop_season = create_test_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
    )

    repository = CropStageRepository(db)

    with pytest.raises(
        ValidationError,
        match="Crop plan can only be regenerated before farming starts",
    ):
        delete_all_stages(
            repository,
            crop_season.id,
        )


# ============================================================
# ALL STAGES COMPLETED
# ============================================================


def test_all_stages_completed_returns_false_for_zero(
    db,
):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    assert (
        all_stages_completed(
            repository,
            crop_season.id,
        )
        is False
    )


def test_all_stages_completed_returns_false_when_pending(
    db,
):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.PENDING,
    )

    assert (
        all_stages_completed(
            repository,
            crop_season.id,
        )
        is False
    )


def test_all_stages_completed_accepts_completed_and_skipped(
    db,
):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    create_stage_direct(
        db,
        crop_season,
        order=1,
        status=CropStageStatus.COMPLETED,
    )

    create_stage_direct(
        db,
        crop_season,
        order=2,
        status=CropStageStatus.SKIPPED,
    )

    assert (
        all_stages_completed(
            repository,
            crop_season.id,
        )
        is True
    )


# ============================================================
# NEXT STAGE
# ============================================================


def test_get_next_stage(db):

    crop_season = create_test_crop_season(db)

    repository = CropStageRepository(db)

    stage1 = create_stage_direct(
        db,
        crop_season,
        order=1,
    )

    stage2 = create_stage_direct(
        db,
        crop_season,
        order=2,
    )

    result = get_next_stage(
        repository,
        stage1,
    )

    assert result is not None
    assert result.id == stage2.id