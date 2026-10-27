from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
)

from app.modules.crop_season.schemas import (
    CropSeasonCancelRequest,
    CropSeasonCreateRequest,
    CropSeasonHarvestRequest,
    CropSeasonUpdateRequest,
    FarmingSeason,
)

from app.modules.crop_season.service import (
    activate_crop_season,
    can_complete_crop_season,
    cancel_crop_season,
    complete_crop_season,
    create_crop_season,
    delete_crop_season,
    get_active_crop_season,
    get_active_crop_seasons,
    get_cancelled_crop_seasons,
    get_crop_season,
    get_crop_seasons,
    get_harvested_crop_seasons,
    get_latest_crop_season,
    get_planned_crop_seasons,
    update_crop_season,
)

from app.modules.crop_stage.models import (
    CropStageStatus,
)

from app.shared.exceptions import (
    CropSeasonNotFoundError,
    ValidationError,
)


# ============================================================
# TEST HELPERS
# ============================================================


def make_crop_season(
    *,
    farm_id=None,
    status=CropSeasonStatus.PLANNED,
    is_active=False,
    sowing_date=date(2026, 6, 1),
    expected_harvest_date=date(2026, 10, 1),
    harvested_date=None,
) -> CropSeason:

    return CropSeason(
        id=uuid4(),
        farm_id=farm_id or uuid4(),

        crop_name="Rice",

        crop_variety="BPT 5204",

        season=FarmingSeason.KHARIF,

        year=2026,

        sowing_date=sowing_date,

        expected_harvest_date=expected_harvest_date,

        harvested_date=harvested_date,

        land_area=1.0,

        land_unit="Acres",

        status=status,

        is_active=is_active,

        notes=None,
    )


def make_stage(
    *,
    crop_season_id,
    stage_order=1,
    status=CropStageStatus.PENDING,
):

    return SimpleNamespace(
        id=uuid4(),

        crop_season_id=crop_season_id,

        stage_order=stage_order,

        status=status,

        started_at=None,

        completed_at=None,
    )


# ============================================================
# MOCK REPOSITORY LIFECYCLE OPERATIONS
# ============================================================
#
# MagicMock does not execute the real repository implementation.
#
# Therefore these helpers simulate:
#
# repository.mark_active()
# repository.mark_harvested()
# repository.mark_cancelled()
#
# ============================================================


def configure_mark_active_mock(
    repository: MagicMock,
) -> None:

    def mark_active(
        crop_season: CropSeason,
    ) -> CropSeason:

        crop_season.status = CropSeasonStatus.ACTIVE

        crop_season.is_active = True

        return crop_season

    repository.mark_active.side_effect = mark_active


def configure_mark_harvested_mock(
    repository: MagicMock,
) -> None:

    def mark_harvested(
        crop_season: CropSeason,
    ) -> CropSeason:

        crop_season.status = CropSeasonStatus.HARVESTED

        crop_season.is_active = False

        return crop_season

    repository.mark_harvested.side_effect = mark_harvested


def configure_mark_cancelled_mock(
    repository: MagicMock,
) -> None:

    def mark_cancelled(
        crop_season: CropSeason,
    ) -> CropSeason:

        crop_season.status = CropSeasonStatus.CANCELLED

        crop_season.is_active = False

        return crop_season

    repository.mark_cancelled.side_effect = mark_cancelled


# ============================================================
# CREATE CROP SEASON
# ============================================================


def test_create_crop_season():

    repository = MagicMock()

    farm_id = uuid4()

    request = CropSeasonCreateRequest(
        crop_name="Rice",
        crop_variety="BPT 5204",
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 1),
        expected_harvest_date=date(2026, 10, 1),
        land_area=1.5,
        land_unit="Acres",
        notes="First crop",
    )

    expected_crop = make_crop_season(
        farm_id=farm_id,
    )

    repository.create.return_value = expected_crop

    result = create_crop_season(
        repository,
        farm_id,
        request,
    )

    assert result is expected_crop

    repository.create.assert_called_once()

    created_crop = repository.create.call_args.args[0]

    assert created_crop.farm_id == farm_id

    assert created_crop.crop_name == "Rice"

    assert created_crop.crop_variety == "BPT 5204"

    assert created_crop.season == FarmingSeason.KHARIF

    assert created_crop.year == 2026

    assert created_crop.sowing_date == date(2026, 6, 1)

    assert created_crop.expected_harvest_date == (
        date(2026, 10, 1)
    )

    assert created_crop.land_area == 1.5

    assert created_crop.land_unit == "Acres"

    assert created_crop.status == CropSeasonStatus.PLANNED

    assert created_crop.is_active is False

    assert created_crop.harvested_date is None

    assert created_crop.notes == "First crop"


def test_create_crop_season_rejects_area_above_farm():

    repository = MagicMock()

    request = CropSeasonCreateRequest(
        crop_name="Rice",
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 1),
        land_area=2.5,
        land_unit="Acres",
    )

    farm = SimpleNamespace(
        land_area=2.0,
        land_unit="Acres",
    )

    with pytest.raises(
        ValidationError,
        match="Crop area cannot exceed farm area.",
    ):

        create_crop_season(
            repository,
            uuid4(),
            request,
            farm=farm,
        )

    repository.create.assert_not_called()


def test_create_crop_season_allows_area_in_different_unit():

    repository = MagicMock()

    request = CropSeasonCreateRequest(
        crop_name="Rice",
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 1),
        land_area=2.5,
        land_unit="Hectares",
    )

    farm = SimpleNamespace(
        land_area=2.0,
        land_unit="Acres",
    )

    expected_crop = make_crop_season()

    repository.create.return_value = expected_crop

    result = create_crop_season(
        repository,
        uuid4(),
        request,
        farm=farm,
    )

    assert result is expected_crop

    repository.create.assert_called_once()


def test_create_crop_season_rolls_back_on_error():

    repository = MagicMock()

    repository.create.side_effect = RuntimeError(
        "Database error"
    )

    farm_id = uuid4()

    request = CropSeasonCreateRequest(
        crop_name="Rice",
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 1),
        land_area=1,
    )

    with pytest.raises(RuntimeError):

        create_crop_season(
            repository,
            farm_id,
            request,
        )

    repository.rollback.assert_called_once()


# ============================================================
# GET CROP SEASON
# ============================================================


def test_get_crop_season():

    repository = MagicMock()

    crop = make_crop_season()

    repository.get_by_id.return_value = crop

    result = get_crop_season(
        repository,
        crop.id,
    )

    assert result is crop

    repository.get_by_id.assert_called_once_with(
        crop.id,
    )


def test_get_crop_season_not_found():

    repository = MagicMock()

    crop_id = uuid4()

    repository.get_by_id.return_value = None

    with pytest.raises(
        CropSeasonNotFoundError,
        match="Crop season not found",
    ):

        get_crop_season(
            repository,
            crop_id,
        )


# ============================================================
# GET ALL CROP SEASONS
# ============================================================


def test_get_crop_seasons():

    repository = MagicMock()

    farm_id = uuid4()

    crops = [
        make_crop_season(
            farm_id=farm_id,
        ),
        make_crop_season(
            farm_id=farm_id,
        ),
    ]

    repository.get_all_by_farm.return_value = crops

    result = get_crop_seasons(
        repository,
        farm_id,
    )

    assert result == crops

    repository.get_all_by_farm.assert_called_once_with(
        farm_id,
    )


# ============================================================
# GET ACTIVE CROP
# ============================================================


def test_get_active_crop_season():

    repository = MagicMock()

    farm_id = uuid4()

    crop = make_crop_season(
        farm_id=farm_id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    repository.get_active_by_farm.return_value = crop

    result = get_active_crop_season(
        repository,
        farm_id,
    )

    assert result is crop

    repository.get_active_by_farm.assert_called_once_with(
        farm_id,
    )


# ============================================================
# GET ALL ACTIVE CROPS
# ============================================================


def test_get_active_crop_seasons():

    repository = MagicMock()

    farm_id = uuid4()

    crops = [
        make_crop_season(
            farm_id=farm_id,
            status=CropSeasonStatus.ACTIVE,
            is_active=True,
        ),
    ]

    repository.get_all_active_by_farm.return_value = crops

    result = get_active_crop_seasons(
        repository,
        farm_id,
    )

    assert result == crops

    repository.get_all_active_by_farm.assert_called_once_with(
        farm_id,
    )


# ============================================================
# GET PLANNED CROPS
# ============================================================


def test_get_planned_crop_seasons():

    repository = MagicMock()

    farm_id = uuid4()

    crops = [
        make_crop_season(
            farm_id=farm_id,
            status=CropSeasonStatus.PLANNED,
            is_active=False,
        ),
    ]

    repository.get_all_planned_by_farm.return_value = crops

    result = get_planned_crop_seasons(
        repository,
        farm_id,
    )

    assert result == crops

    repository.get_all_planned_by_farm.assert_called_once_with(
        farm_id,
    )


# ============================================================
# GET HARVESTED CROPS
# ============================================================


def test_get_harvested_crop_seasons():

    repository = MagicMock()

    farm_id = uuid4()

    crops = [
        make_crop_season(
            farm_id=farm_id,
            status=CropSeasonStatus.HARVESTED,
            is_active=False,
            harvested_date=date(2026, 10, 1),
        ),
    ]

    repository.get_all_harvested_by_farm.return_value = crops

    result = get_harvested_crop_seasons(
        repository,
        farm_id,
    )

    assert result == crops

    repository.get_all_harvested_by_farm.assert_called_once_with(
        farm_id,
    )


# ============================================================
# GET CANCELLED CROPS
# ============================================================


def test_get_cancelled_crop_seasons():

    repository = MagicMock()

    farm_id = uuid4()

    crops = [
        make_crop_season(
            farm_id=farm_id,
            status=CropSeasonStatus.CANCELLED,
            is_active=False,
        ),
    ]

    repository.get_all_cancelled_by_farm.return_value = crops

    result = get_cancelled_crop_seasons(
        repository,
        farm_id,
    )

    assert result == crops

    repository.get_all_cancelled_by_farm.assert_called_once_with(
        farm_id,
    )


# ============================================================
# GET LATEST CROP
# ============================================================


def test_get_latest_crop_season():

    repository = MagicMock()

    farm_id = uuid4()

    crop = make_crop_season(
        farm_id=farm_id,
    )

    repository.get_latest_by_farm.return_value = crop

    result = get_latest_crop_season(
        repository,
        farm_id,
    )

    assert result is crop

    repository.get_latest_by_farm.assert_called_once_with(
        farm_id,
    )


def test_get_latest_crop_season_empty():

    repository = MagicMock()

    farm_id = uuid4()

    repository.get_latest_by_farm.return_value = None

    result = get_latest_crop_season(
        repository,
        farm_id,
    )

    assert result is None


# ============================================================
# UPDATE CROP SEASON
# ============================================================


def test_update_crop_season():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.PLANNED,
        is_active=False,
    )

    request = CropSeasonUpdateRequest(
        crop_name="Wheat",
        land_area=2.0,
    )

    repository.update.return_value = crop

    result = update_crop_season(
        repository,
        crop,
        request,
    )

    assert result is crop

    assert crop.crop_name == "Wheat"

    assert crop.land_area == 2.0

    assert crop.status == CropSeasonStatus.PLANNED

    assert crop.is_active is False

    repository.update.assert_called_once_with(
        crop,
    )


@pytest.mark.parametrize(
    "status",
    [
        CropSeasonStatus.ACTIVE,
        CropSeasonStatus.HARVESTED,
        CropSeasonStatus.CANCELLED,
    ],
)
def test_update_crop_season_rejects_non_planned(
    status,
):

    repository = MagicMock()

    crop = make_crop_season(
        status=status,
        is_active=(
            status == CropSeasonStatus.ACTIVE
        ),
    )

    request = CropSeasonUpdateRequest(
        crop_name="Wheat",
    )

    with pytest.raises(
        ValidationError,
        match="Only a planned crop season can be edited",
    ):

        update_crop_season(
            repository,
            crop,
            request,
        )

    repository.update.assert_not_called()


def test_update_crop_season_valid_dates():

    repository = MagicMock()

    crop = make_crop_season(
        sowing_date=date(2026, 6, 1),
        expected_harvest_date=date(2026, 10, 1),
    )

    request = CropSeasonUpdateRequest(
        sowing_date=date(2026, 6, 15),
        expected_harvest_date=date(2026, 10, 15),
    )

    repository.update.return_value = crop

    result = update_crop_season(
        repository,
        crop,
        request,
    )

    assert result is crop

    assert crop.sowing_date == date(2026, 6, 15)

    assert crop.expected_harvest_date == (
        date(2026, 10, 15)
    )


def test_update_crop_season_rejects_invalid_final_dates():

    repository = MagicMock()

    crop = make_crop_season(
        sowing_date=date(2026, 6, 1),
    )

    request = CropSeasonUpdateRequest(
        expected_harvest_date=date(2026, 5, 1),
    )

    with pytest.raises(
        ValidationError,
        match="Expected harvest date",
    ):

        update_crop_season(
            repository,
            crop,
            request,
        )

    repository.update.assert_not_called()


def test_update_crop_season_rolls_back_on_error():

    repository = MagicMock()

    crop = make_crop_season()

    request = CropSeasonUpdateRequest(
        crop_name="Wheat",
    )

    repository.update.side_effect = RuntimeError(
        "Database error"
    )

    with pytest.raises(RuntimeError):

        update_crop_season(
            repository,
            crop,
            request,
        )

    repository.rollback.assert_called_once()


def test_update_crop_season_rejects_changes_after_plan():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season()

    stage_repository.get_all_by_crop_season.return_value = [
        make_stage(crop_season_id=crop.id),
    ]

    request = CropSeasonUpdateRequest(
        crop_name="Wheat",
    )

    with pytest.raises(
        ValidationError,
        match="after a crop plan has been generated",
    ):

        update_crop_season(
            repository,
            crop,
            request,
            stage_repository=stage_repository,
        )

    repository.update.assert_not_called()


def test_update_crop_season_allows_notes_after_plan():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season()

    stage_repository.get_all_by_crop_season.return_value = [
        make_stage(crop_season_id=crop.id),
    ]

    repository.update.return_value = crop

    request = CropSeasonUpdateRequest(
        notes="Adjusted after plan review.",
    )

    result = update_crop_season(
        repository,
        crop,
        request,
        stage_repository=stage_repository,
    )

    assert result is crop

    assert crop.notes == "Adjusted after plan review."


def test_update_sowing_date_synchronizes_year():

    repository = MagicMock()

    crop = make_crop_season(
        sowing_date=date(2026, 6, 1),
        expected_harvest_date=date(2027, 10, 1),
    )

    repository.update.return_value = crop

    request = CropSeasonUpdateRequest(
        sowing_date=date(2027, 6, 1),
    )

    result = update_crop_season(
        repository,
        crop,
        request,
    )

    assert result is crop

    assert crop.sowing_date == date(2027, 6, 1)

    assert crop.year == 2027


# ============================================================
# ACTIVATE CROP SEASON
# ============================================================


def test_activate_crop_season():

    repository = MagicMock()

    stage_repository = MagicMock()

    farm_id = uuid4()

    crop = make_crop_season(
        farm_id=farm_id,
        status=CropSeasonStatus.PLANNED,
        is_active=False,
    )

    first_stage = make_stage(
        crop_season_id=crop.id,
        stage_order=1,
        status=CropStageStatus.PENDING,
    )

    repository.get_active_by_farm.return_value = None

    stage_repository.get_first_pending_stage.return_value = (
        first_stage
    )

    stage_repository.get_active_by_crop_season.return_value = None

    configure_mark_active_mock(
        repository,
    )

    result = activate_crop_season(
        repository,
        stage_repository,
        crop,
    )

    assert result is crop

    assert crop.status == CropSeasonStatus.ACTIVE

    assert crop.is_active is True

    assert first_stage.status == CropStageStatus.ACTIVE

    assert first_stage.started_at == crop.sowing_date

    assert first_stage.completed_at is None

    repository.mark_active.assert_called_once_with(
        crop,
    )

    repository.flush.assert_called_once()

    repository.commit.assert_called_once()

    repository.refresh.assert_called_once_with(
        crop,
    )

    stage_repository.refresh.assert_called_once_with(
        first_stage,
    )


def test_activate_active_crop_is_idempotent():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    result = activate_crop_season(
        repository,
        stage_repository,
        crop,
    )

    assert result is crop

    assert crop.status == CropSeasonStatus.ACTIVE

    assert crop.is_active is True

    repository.get_active_by_farm.assert_not_called()

    stage_repository.get_first_pending_stage.assert_not_called()

    repository.mark_active.assert_not_called()


def test_activate_active_crop_repairs_is_active():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=False,
    )

    result = activate_crop_season(
        repository,
        stage_repository,
        crop,
    )

    assert result is crop

    assert crop.status == CropSeasonStatus.ACTIVE

    assert crop.is_active is True

    repository.flush.assert_called_once()

    repository.commit.assert_called_once()

    repository.refresh.assert_called_once_with(
        crop,
    )


@pytest.mark.parametrize(
    "status",
    [
        CropSeasonStatus.HARVESTED,
        CropSeasonStatus.CANCELLED,
    ],
)
def test_activate_rejects_invalid_status(
    status,
):

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=status,
        is_active=False,
    )

    with pytest.raises(
        ValidationError,
        match="Only a planned crop season can be activated",
    ):

        activate_crop_season(
            repository,
            stage_repository,
            crop,
        )

    repository.mark_active.assert_not_called()


def test_activate_rejects_another_active_crop():

    repository = MagicMock()

    stage_repository = MagicMock()

    farm_id = uuid4()

    crop = make_crop_season(
        farm_id=farm_id,
        status=CropSeasonStatus.PLANNED,
    )

    active_crop = make_crop_season(
        farm_id=farm_id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    repository.get_active_by_farm.return_value = active_crop

    with pytest.raises(
        ValidationError,
        match="Another crop season is already active",
    ):

        activate_crop_season(
            repository,
            stage_repository,
            crop,
        )

    repository.mark_active.assert_not_called()


def test_activate_allows_same_crop_as_active_result():

    repository = MagicMock()

    stage_repository = MagicMock()

    farm_id = uuid4()

    crop = make_crop_season(
        farm_id=farm_id,
        status=CropSeasonStatus.PLANNED,
        is_active=False,
    )

    first_stage = make_stage(
        crop_season_id=crop.id,
        stage_order=1,
        status=CropStageStatus.PENDING,
    )

    repository.get_active_by_farm.return_value = crop

    stage_repository.get_first_pending_stage.return_value = (
        first_stage
    )

    stage_repository.get_active_by_crop_season.return_value = None

    configure_mark_active_mock(
        repository,
    )

    result = activate_crop_season(
        repository,
        stage_repository,
        crop,
    )

    assert result is crop

    assert crop.status == CropSeasonStatus.ACTIVE

    assert crop.is_active is True


def test_activate_rejects_missing_crop_plan():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.PLANNED,
    )

    repository.get_active_by_farm.return_value = None

    stage_repository.get_first_pending_stage.return_value = None

    with pytest.raises(
        ValidationError,
        match="Crop plan has not been generated",
    ):

        activate_crop_season(
            repository,
            stage_repository,
            crop,
        )

    repository.mark_active.assert_not_called()


def test_activate_rejects_wrong_stage_ownership():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season()

    another_crop_id = uuid4()

    first_stage = make_stage(
        crop_season_id=another_crop_id,
        stage_order=1,
        status=CropStageStatus.PENDING,
    )

    repository.get_active_by_farm.return_value = None

    stage_repository.get_first_pending_stage.return_value = (
        first_stage
    )

    with pytest.raises(
        ValidationError,
        match="does not belong",
    ):

        activate_crop_season(
            repository,
            stage_repository,
            crop,
        )

    repository.mark_active.assert_not_called()


def test_activate_rejects_wrong_stage_order():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season()

    first_stage = make_stage(
        crop_season_id=crop.id,
        stage_order=2,
        status=CropStageStatus.PENDING,
    )

    repository.get_active_by_farm.return_value = None

    stage_repository.get_first_pending_stage.return_value = (
        first_stage
    )

    with pytest.raises(
        ValidationError,
        match="stage order 1",
    ):

        activate_crop_season(
            repository,
            stage_repository,
            crop,
        )

    repository.mark_active.assert_not_called()


def test_activate_rejects_non_pending_first_stage():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season()

    first_stage = make_stage(
        crop_season_id=crop.id,
        stage_order=1,
        status=CropStageStatus.COMPLETED,
    )

    repository.get_active_by_farm.return_value = None

    stage_repository.get_first_pending_stage.return_value = (
        first_stage
    )

    with pytest.raises(
        ValidationError,
        match="not available for activation",
    ):

        activate_crop_season(
            repository,
            stage_repository,
            crop,
        )

    repository.mark_active.assert_not_called()


def test_activate_rejects_existing_active_stage():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season()

    first_stage = make_stage(
        crop_season_id=crop.id,
        stage_order=1,
        status=CropStageStatus.PENDING,
    )

    active_stage = make_stage(
        crop_season_id=crop.id,
        stage_order=1,
        status=CropStageStatus.ACTIVE,
    )

    repository.get_active_by_farm.return_value = None

    stage_repository.get_first_pending_stage.return_value = (
        first_stage
    )

    stage_repository.get_active_by_crop_season.return_value = (
        active_stage
    )

    with pytest.raises(
        ValidationError,
        match="already has an active stage",
    ):

        activate_crop_season(
            repository,
            stage_repository,
            crop,
        )

    repository.mark_active.assert_not_called()


def test_activate_rolls_back_on_error():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season()

    first_stage = make_stage(
        crop_season_id=crop.id,
        stage_order=1,
        status=CropStageStatus.PENDING,
    )

    repository.get_active_by_farm.return_value = None

    stage_repository.get_first_pending_stage.return_value = (
        first_stage
    )

    stage_repository.get_active_by_crop_season.return_value = None

    configure_mark_active_mock(
        repository,
    )

    repository.commit.side_effect = RuntimeError(
        "Database error"
    )

    with pytest.raises(RuntimeError):

        activate_crop_season(
            repository,
            stage_repository,
            crop,
        )

    repository.rollback.assert_called_once()


# ============================================================
# CAN COMPLETE CROP SEASON
# ============================================================


def test_can_complete_crop_season_returns_true():

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    stage_repository.get_active_by_crop_season.return_value = None

    stage_repository.all_finished.return_value = True

    result = can_complete_crop_season(
        stage_repository,
        crop,
    )

    assert result is True

    stage_repository.get_active_by_crop_season.assert_called_once_with(
        crop.id,
    )

    stage_repository.all_finished.assert_called_once_with(
        crop.id,
    )


def test_can_complete_crop_season_returns_false_for_planned():

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.PLANNED,
        is_active=False,
    )

    result = can_complete_crop_season(
        stage_repository,
        crop,
    )

    assert result is False

    stage_repository.get_active_by_crop_season.assert_not_called()

    stage_repository.all_finished.assert_not_called()


def test_can_complete_crop_season_returns_false_for_harvested():

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.HARVESTED,
        is_active=False,
        harvested_date=date(2026, 10, 1),
    )

    result = can_complete_crop_season(
        stage_repository,
        crop,
    )

    assert result is False

    stage_repository.get_active_by_crop_season.assert_not_called()


def test_can_complete_crop_season_returns_false_for_cancelled():

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.CANCELLED,
        is_active=False,
    )

    result = can_complete_crop_season(
        stage_repository,
        crop,
    )

    assert result is False

    stage_repository.get_active_by_crop_season.assert_not_called()


def test_can_complete_returns_false_when_active_stage_exists():

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    active_stage = make_stage(
        crop_season_id=crop.id,
        status=CropStageStatus.ACTIVE,
    )

    stage_repository.get_active_by_crop_season.return_value = (
        active_stage
    )

    result = can_complete_crop_season(
        stage_repository,
        crop,
    )

    assert result is False

    stage_repository.all_finished.assert_not_called()


def test_can_complete_returns_false_when_stages_not_finished():

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    stage_repository.get_active_by_crop_season.return_value = None

    stage_repository.all_finished.return_value = False

    result = can_complete_crop_season(
        stage_repository,
        crop,
    )

    assert result is False

    stage_repository.all_finished.assert_called_once_with(
        crop.id,
    )


# ============================================================
# COMPLETE / HARVEST CROP SEASON
# ============================================================


def test_complete_crop_season():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    stage_repository.get_active_by_crop_season.return_value = None

    stage_repository.all_finished.return_value = True

    configure_mark_harvested_mock(
        repository,
    )

    result = complete_crop_season(
        repository,
        stage_repository,
        crop,
    )

    assert result is crop

    assert crop.status == CropSeasonStatus.HARVESTED

    assert crop.is_active is False

    repository.mark_harvested.assert_called_once_with(
        crop,
    )

    repository.commit.assert_called_once()

    repository.refresh.assert_called_once_with(
        crop,
    )


def test_complete_crop_season_applies_harvest_request():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    stage_repository.get_active_by_crop_season.return_value = None

    stage_repository.all_finished.return_value = True

    configure_mark_harvested_mock(
        repository,
    )

    request = CropSeasonHarvestRequest(
        harvested_date=date(2026, 9, 30),
        notes="Harvested before rain.",
    )

    result = complete_crop_season(
        repository,
        stage_repository,
        crop,
        request=request,
    )

    assert result is crop

    assert crop.harvested_date == date(2026, 9, 30)

    assert crop.notes == "Harvested before rain."


def test_complete_crop_season_rejects_non_active():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.PLANNED,
        is_active=False,
    )

    with pytest.raises(
        ValidationError,
        match="Only an active crop season can be harvested",
    ):

        complete_crop_season(
            repository,
            stage_repository,
            crop,
        )

    repository.mark_harvested.assert_not_called()


@pytest.mark.parametrize(
    "status",
    [
        CropSeasonStatus.PLANNED,
        CropSeasonStatus.HARVESTED,
        CropSeasonStatus.CANCELLED,
    ],
)
def test_complete_rejects_all_non_active_statuses(
    status,
):

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=status,
        is_active=False,
    )

    with pytest.raises(
        ValidationError,
        match="Only an active crop season can be harvested",
    ):

        complete_crop_season(
            repository,
            stage_repository,
            crop,
        )


def test_complete_rejects_active_stage():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    active_stage = make_stage(
        crop_season_id=crop.id,
        status=CropStageStatus.ACTIVE,
    )

    stage_repository.get_active_by_crop_season.return_value = (
        active_stage
    )

    with pytest.raises(
        ValidationError,
        match="current crop stage must be completed",
    ):

        complete_crop_season(
            repository,
            stage_repository,
            crop,
        )

    stage_repository.all_finished.assert_not_called()

    repository.mark_harvested.assert_not_called()


def test_complete_rejects_unfinished_stages():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    stage_repository.get_active_by_crop_season.return_value = None

    stage_repository.all_finished.return_value = False

    with pytest.raises(
        ValidationError,
        match="All crop stages must be completed or skipped",
    ):

        complete_crop_season(
            repository,
            stage_repository,
            crop,
        )

    repository.mark_harvested.assert_not_called()

    repository.commit.assert_not_called()


def test_complete_crop_season_rolls_back_on_error():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    stage_repository.get_active_by_crop_season.return_value = None

    stage_repository.all_finished.return_value = True

    configure_mark_harvested_mock(
        repository,
    )

    repository.commit.side_effect = RuntimeError(
        "Database error"
    )

    with pytest.raises(RuntimeError):

        complete_crop_season(
            repository,
            stage_repository,
            crop,
        )

    repository.rollback.assert_called_once()


# ============================================================
# CANCEL CROP SEASON
# ============================================================


def test_cancel_planned_crop():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.PLANNED,
        is_active=False,
    )

    configure_mark_cancelled_mock(
        repository,
    )

    result = cancel_crop_season(
        repository,
        crop,
    )

    assert result is crop

    assert crop.status == CropSeasonStatus.CANCELLED

    assert crop.is_active is False

    repository.mark_cancelled.assert_called_once_with(
        crop,
    )

    repository.commit.assert_called_once()

    repository.refresh.assert_called_once_with(
        crop,
    )


def test_cancel_active_crop():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    configure_mark_cancelled_mock(
        repository,
    )

    result = cancel_crop_season(
        repository,
        crop,
    )

    assert result is crop

    assert crop.status == CropSeasonStatus.CANCELLED

    assert crop.is_active is False

    repository.mark_cancelled.assert_called_once_with(
        crop,
    )

    repository.commit.assert_called_once()

    repository.refresh.assert_called_once_with(
        crop,
    )


def test_cancel_records_reason_and_skips_active_stage():

    repository = MagicMock()

    stage_repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    active_stage = make_stage(
        crop_season_id=crop.id,
        status=CropStageStatus.ACTIVE,
    )

    stage_repository.get_active_by_crop_season.return_value = (
        active_stage
    )

    configure_mark_cancelled_mock(
        repository,
    )

    request = CropSeasonCancelRequest(
        reason="  Heavy rain damaged the crop.  ",
    )

    result = cancel_crop_season(
        repository,
        crop,
        request=request,
        stage_repository=stage_repository,
    )

    assert result is crop

    assert crop.cancellation_reason == (
        "Heavy rain damaged the crop."
    )

    assert active_stage.status == CropStageStatus.SKIPPED

    assert active_stage.completed_at == date.today()


def test_cancel_harvested_crop_rejected():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.HARVESTED,
        is_active=False,
        harvested_date=date(2026, 10, 1),
    )

    with pytest.raises(
        ValidationError,
        match="Harvested crop season cannot be cancelled",
    ):

        cancel_crop_season(
            repository,
            crop,
        )

    repository.mark_cancelled.assert_not_called()

    repository.commit.assert_not_called()


def test_cancel_already_cancelled_is_idempotent():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.CANCELLED,
        is_active=False,
    )

    result = cancel_crop_season(
        repository,
        crop,
    )

    assert result is crop

    assert crop.status == CropSeasonStatus.CANCELLED

    assert crop.is_active is False

    repository.mark_cancelled.assert_not_called()

    repository.commit.assert_not_called()

    repository.refresh.assert_not_called()


def test_cancel_rolls_back_on_error():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.PLANNED,
    )

    configure_mark_cancelled_mock(
        repository,
    )

    repository.commit.side_effect = RuntimeError(
        "Database error"
    )

    with pytest.raises(RuntimeError):

        cancel_crop_season(
            repository,
            crop,
        )

    repository.rollback.assert_called_once()


# ============================================================
# DELETE CROP SEASON
# ============================================================


def test_delete_planned_crop():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.PLANNED,
    )

    result = delete_crop_season(
        repository,
        crop,
    )

    assert result is None

    repository.delete.assert_called_once_with(
        crop,
    )


def test_delete_cancelled_crop():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.CANCELLED,
    )

    result = delete_crop_season(
        repository,
        crop,
    )

    assert result is None

    repository.delete.assert_called_once_with(
        crop,
    )


def test_delete_active_crop_rejected():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    with pytest.raises(
        ValidationError,
        match="Active crop season cannot be deleted",
    ):

        delete_crop_season(
            repository,
            crop,
        )

    repository.delete.assert_not_called()


def test_delete_harvested_crop_rejected():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.HARVESTED,
        is_active=False,
        harvested_date=date(2026, 10, 1),
    )

    with pytest.raises(
        ValidationError,
        match="Harvested crop season cannot be deleted",
    ):

        delete_crop_season(
            repository,
            crop,
        )

    repository.delete.assert_not_called()


def test_delete_cancelled_crop_allowed():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.CANCELLED,
        is_active=False,
    )

    delete_crop_season(
        repository,
        crop,
    )

    repository.delete.assert_called_once_with(
        crop,
    )


def test_delete_rolls_back_on_error():

    repository = MagicMock()

    crop = make_crop_season(
        status=CropSeasonStatus.PLANNED,
    )

    repository.delete.side_effect = RuntimeError(
        "Database error"
    )

    with pytest.raises(RuntimeError):

        delete_crop_season(
            repository,
            crop,
        )

    repository.rollback.assert_called_once()