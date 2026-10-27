from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from fastapi import HTTPException

from app.modules.activity.models import (
    ActivityPriority,
    ActivityType,
)

from app.modules.crop_plan import router

from app.modules.crop_plan.schemas import (
    CropPlanGenerateRequest,
    CropPlanStageRequest,
)

from app.modules.crop_season.models import (
    CropSeasonStatus,
)


# ============================================================
# HELPERS
# ============================================================


def make_farmer():
    return SimpleNamespace(
        id=__import__("uuid").uuid4(),
    )


def make_user():
    return SimpleNamespace(
        id=__import__("uuid").uuid4(),
    )


def make_crop(
    farmer_id,
    *,
    status=CropSeasonStatus.PLANNED,
):

    farm = SimpleNamespace(
        id=__import__("uuid").uuid4(),
        farmer_id=farmer_id,
    )

    return SimpleNamespace(
        id=__import__("uuid").uuid4(),
        farm=farm,
        status=status,
        sowing_date=date(2026, 8, 10),
    )


def make_request():

    return CropPlanGenerateRequest(
        start_date=date(2026, 8, 10),
        stages=[
            CropPlanStageRequest(
                name="Vegetative Stage",
                description="Vegetative growth",
                stage_order=1,
                start_day=1,
                end_day=15,
                activities=[],
            ),
        ],
    )


def make_db():
    return MagicMock()


# ============================================================
# FARMER
# ============================================================


def test_get_farmer_returns_farmer(
    monkeypatch,
):

    farmer = make_farmer()

    repository = MagicMock()
    repository.get_by_user_id.return_value = farmer

    monkeypatch.setattr(
        router,
        "FarmerRepository",
        lambda db: repository,
    )

    result = router._get_farmer(
        make_db(),
        make_user(),
    )

    assert result is farmer


def test_get_farmer_not_found(
    monkeypatch,
):

    repository = MagicMock()
    repository.get_by_user_id.return_value = None

    monkeypatch.setattr(
        router,
        "FarmerRepository",
        lambda db: repository,
    )

    with pytest.raises(HTTPException) as exc:

        router._get_farmer(
            make_db(),
            make_user(),
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Farmer profile not found."


# ============================================================
# CROP SEASON
# ============================================================


def test_get_crop_season_returns_crop(
    monkeypatch,
):

    farmer = make_farmer()

    crop = make_crop(
        farmer.id,
    )

    repository = MagicMock()
    repository.get_by_id.return_value = crop

    monkeypatch.setattr(
        router,
        "CropSeasonRepository",
        lambda db: repository,
    )

    result = router._get_crop_season(
        make_db(),
        crop.id,
    )

    assert result is crop


def test_get_crop_season_not_found(
    monkeypatch,
):

    repository = MagicMock()
    repository.get_by_id.return_value = None

    monkeypatch.setattr(
        router,
        "CropSeasonRepository",
        lambda db: repository,
    )

    crop_id = __import__("uuid").uuid4()

    with pytest.raises(HTTPException) as exc:

        router._get_crop_season(
            make_db(),
            crop_id,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Crop season not found."


# ============================================================
# CROP ACCESS
# ============================================================


def test_verify_crop_access_allows_owner():

    farmer = make_farmer()

    crop = make_crop(
        farmer.id,
    )

    router._verify_crop_access(
        crop,
        farmer,
    )


def test_verify_crop_access_rejects_other_farmer():

    owner = make_farmer()
    another_farmer = make_farmer()

    crop = make_crop(
        owner.id,
    )

    with pytest.raises(HTTPException) as exc:

        router._verify_crop_access(
            crop,
            another_farmer,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Access denied."


def test_verify_crop_access_rejects_missing_farm():

    farmer = make_farmer()

    crop = SimpleNamespace(
        farm=None,
    )

    with pytest.raises(HTTPException) as exc:

        router._verify_crop_access(
            crop,
            farmer,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Farm not found."


# ============================================================
# PLANNED CROP
# ============================================================


def test_require_planned_crop_accepts_planned():

    crop = SimpleNamespace(
        status=CropSeasonStatus.PLANNED,
    )

    router._require_planned_crop(crop)


@pytest.mark.parametrize(
    "status",
    [
        CropSeasonStatus.ACTIVE,
        CropSeasonStatus.HARVESTED,
        CropSeasonStatus.CANCELLED,
    ],
)
def test_require_planned_crop_rejects_non_planned(
    status,
):

    crop = SimpleNamespace(
        status=status,
    )

    with pytest.raises(HTTPException) as exc:

        router._require_planned_crop(crop)

    assert exc.value.status_code == 400


# ============================================================
# GENERATE ENDPOINT
# ============================================================


def test_generate_crop_plan_endpoint(
    monkeypatch,
):

    farmer = make_farmer()
    user = make_user()
    crop = make_crop(
        farmer.id,
    )

    plan = SimpleNamespace(
        crop_season_id=crop.id,
        status=CropSeasonStatus.PLANNED,
        start_date=date(2026, 8, 10),
        stages=[],
        total_stages=0,
        total_activities=0,
    )

    monkeypatch.setattr(
        router,
        "_get_farmer",
        lambda db, current_user: farmer,
    )

    monkeypatch.setattr(
        router,
        "_get_crop_season",
        lambda db, crop_season_id: crop,
    )

    repository = MagicMock()

    monkeypatch.setattr(
        router,
        "ActivityRepository",
        lambda db: repository,
    )

    monkeypatch.setattr(
        router,
        "generate_crop_plan",
        lambda activity_repository, crop_season_id, request: plan,
    )

    response = router.generate_crop_plan_endpoint(
        crop_season_id=crop.id,
        request=make_request(),
        current_user=user,
        db=make_db(),
    )

    assert response.success is True
    assert response.message == "Crop plan generated successfully."
    assert response.data is plan


def test_generate_crop_plan_endpoint_rejects_non_planned(
    monkeypatch,
):

    farmer = make_farmer()

    crop = make_crop(
        farmer.id,
        status=CropSeasonStatus.ACTIVE,
    )

    monkeypatch.setattr(
        router,
        "_get_farmer",
        lambda db, current_user: farmer,
    )

    monkeypatch.setattr(
        router,
        "_get_crop_season",
        lambda db, crop_season_id: crop,
    )

    with pytest.raises(HTTPException) as exc:

        router.generate_crop_plan_endpoint(
            crop_season_id=crop.id,
            request=make_request(),
            current_user=make_user(),
            db=make_db(),
        )

    assert exc.value.status_code == 400


def test_generate_crop_plan_endpoint_rejects_service_error(
    monkeypatch,
):

    farmer = make_farmer()

    crop = make_crop(
        farmer.id,
    )

    monkeypatch.setattr(
        router,
        "_get_farmer",
        lambda db, current_user: farmer,
    )

    monkeypatch.setattr(
        router,
        "_get_crop_season",
        lambda db, crop_season_id: crop,
    )

    repository = MagicMock()

    monkeypatch.setattr(
        router,
        "ActivityRepository",
        lambda db: repository,
    )

    monkeypatch.setattr(
        router,
        "generate_crop_plan",
        MagicMock(
            side_effect=ValueError(
                "Invalid crop plan",
            ),
        ),
    )

    with pytest.raises(HTTPException) as exc:

        router.generate_crop_plan_endpoint(
            crop_season_id=crop.id,
            request=make_request(),
            current_user=make_user(),
            db=make_db(),
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid crop plan"


# ============================================================
# REGENERATE ENDPOINT
# ============================================================


def test_regenerate_crop_plan_endpoint(
    monkeypatch,
):

    farmer = make_farmer()

    crop = make_crop(
        farmer.id,
    )

    plan = SimpleNamespace(
        crop_season_id=crop.id,
        status=CropSeasonStatus.PLANNED,
        start_date=date(2026, 8, 10),
        stages=[],
        total_stages=0,
        total_activities=0,
    )

    monkeypatch.setattr(
        router,
        "_get_farmer",
        lambda db, current_user: farmer,
    )

    monkeypatch.setattr(
        router,
        "_get_crop_season",
        lambda db, crop_season_id: crop,
    )

    repository = MagicMock()

    monkeypatch.setattr(
        router,
        "ActivityRepository",
        lambda db: repository,
    )

    monkeypatch.setattr(
        router,
        "regenerate_crop_plan",
        lambda activity_repository, crop_season_id, request: plan,
    )

    response = router.regenerate_crop_plan_endpoint(
        crop_season_id=crop.id,
        request=make_request(),
        current_user=make_user(),
        db=make_db(),
    )

    assert response.success is True
    assert response.message == (
        "Crop plan regenerated successfully."
    )


def test_regenerate_crop_plan_endpoint_rejects_non_planned(
    monkeypatch,
):

    farmer = make_farmer()

    crop = make_crop(
        farmer.id,
        status=CropSeasonStatus.HARVESTED,
    )

    monkeypatch.setattr(
        router,
        "_get_farmer",
        lambda db, current_user: farmer,
    )

    monkeypatch.setattr(
        router,
        "_get_crop_season",
        lambda db, crop_season_id: crop,
    )

    with pytest.raises(HTTPException) as exc:

        router.regenerate_crop_plan_endpoint(
            crop_season_id=crop.id,
            request=make_request(),
            current_user=make_user(),
            db=make_db(),
        )

    assert exc.value.status_code == 400


def test_regenerate_crop_plan_endpoint_converts_service_error(
    monkeypatch,
):

    farmer = make_farmer()

    crop = make_crop(
        farmer.id,
    )

    monkeypatch.setattr(
        router,
        "_get_farmer",
        lambda db, current_user: farmer,
    )

    monkeypatch.setattr(
        router,
        "_get_crop_season",
        lambda db, crop_season_id: crop,
    )

    repository = MagicMock()

    monkeypatch.setattr(
        router,
        "ActivityRepository",
        lambda db: repository,
    )

    monkeypatch.setattr(
        router,
        "regenerate_crop_plan",
        MagicMock(
            side_effect=ValueError(
                "Invalid regeneration request",
            ),
        ),
    )

    with pytest.raises(HTTPException) as exc:

        router.regenerate_crop_plan_endpoint(
            crop_season_id=crop.id,
            request=make_request(),
            current_user=make_user(),
            db=make_db(),
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid regeneration request"


# ============================================================
# GET ENDPOINT
# ============================================================


def test_get_crop_plan_endpoint(
    monkeypatch,
):

    farmer = make_farmer()

    crop = make_crop(
        farmer.id,
    )

    plan = SimpleNamespace(
        crop_season_id=crop.id,
        status=CropSeasonStatus.PLANNED,
        start_date=date(2026, 8, 10),
        stages=[],
        total_stages=0,
        total_activities=0,
    )

    monkeypatch.setattr(
        router,
        "_get_farmer",
        lambda db, current_user: farmer,
    )

    monkeypatch.setattr(
        router,
        "_get_crop_season",
        lambda db, crop_season_id: crop,
    )

    repository = MagicMock()

    monkeypatch.setattr(
        router,
        "ActivityRepository",
        lambda db: repository,
    )

    monkeypatch.setattr(
        router,
        "get_crop_plan",
        lambda activity_repository, crop_season_id: plan,
    )

    response = router.get_crop_plan_endpoint(
        crop_season_id=crop.id,
        current_user=make_user(),
        db=make_db(),
    )

    assert response.success is True
    assert response.message == (
        "Crop plan retrieved successfully."
    )
    assert response.data is plan


def test_get_crop_plan_endpoint_not_found(
    monkeypatch,
):

    farmer = make_farmer()

    crop = make_crop(
        farmer.id,
    )

    monkeypatch.setattr(
        router,
        "_get_farmer",
        lambda db, current_user: farmer,
    )

    monkeypatch.setattr(
        router,
        "_get_crop_season",
        lambda db, crop_season_id: crop,
    )

    repository = MagicMock()

    monkeypatch.setattr(
        router,
        "ActivityRepository",
        lambda db: repository,
    )

    monkeypatch.setattr(
        router,
        "get_crop_plan",
        MagicMock(
            side_effect=ValueError(
                "No crop plan has been generated yet.",
            ),
        ),
    )

    with pytest.raises(HTTPException) as exc:

        router.get_crop_plan_endpoint(
            crop_season_id=crop.id,
            current_user=make_user(),
            db=make_db(),
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == (
        "No crop plan has been generated yet."
    )