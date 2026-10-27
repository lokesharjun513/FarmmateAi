from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.auth import get_current_user
from app.database.session import get_db

from app.modules.identity.models import User
from app.modules.farmer.models import Farmer
from app.modules.farm.models import Farm

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
    FarmingSeason,
)

from app.modules.crop_stage.models import (
    CropStage,
    CropStageStatus,
)


# ============================================================
# CONSTANTS
# ============================================================

BASE_URL = "/api/v1/crop-stages"


# ============================================================
# USER HELPERS
# ============================================================


def create_user(
    db,
    *,
    full_name="Test Farmer",
    mobile=None,
    email=None,
    is_active=True,
):
    user = User(
        id=uuid4(),
        full_name=full_name,
        mobile=mobile or f"{uuid4().hex[:10]}",
        email=email or f"{uuid4().hex[:10]}@test.com",
        password_hash="test-password-hash",
        is_active=is_active,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# FARMER HELPERS
# ============================================================


def create_farmer(
    db,
    user,
):
    farmer = Farmer(
        id=uuid4(),
        user_id=user.id,
        preferred_language="English",
        experience_years=5,
        profile_completion=100,
        onboarding_completed=True,
    )

    db.add(farmer)
    db.commit()
    db.refresh(farmer)

    return farmer


# ============================================================
# FARM HELPERS
# ============================================================


def create_farm(
    db,
    farmer,
):
    farm = Farm(
        id=uuid4(),
        farmer_id=farmer.id,
        farm_name="Test Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Test Mandal",
        village="Test Village",
        latitude=None,
        longitude=None,
        land_area=1.0,
        land_unit="Acres",
        soil_type="Clay",
        water_source="Borewell",
        water_availability="HIGH",
        irrigation_method="Flood",
        is_primary=True,
    )

    db.add(farm)
    db.commit()
    db.refresh(farm)

    return farm


# ============================================================
# CROP SEASON HELPERS
# ============================================================


def create_crop_season(
    db,
    farm,
    *,
    status=CropSeasonStatus.PLANNED,
):
    crop = CropSeason(
        id=uuid4(),
        farm_id=farm.id,
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

    db.add(crop)
    db.commit()
    db.refresh(crop)

    return crop


# ============================================================
# CROP STAGE HELPERS
# ============================================================


def create_stage(
    db,
    crop,
    *,
    order=1,
    stage_status=CropStageStatus.PENDING,
):
    stage = CropStage(
        id=uuid4(),
        crop_season_id=crop.id,
        name=f"Stage {order}",
        description=f"Stage {order} description",
        stage_order=order,
        start_day=order,
        end_day=order + 5,
        status=stage_status,
        started_at=(
            date.today()
            if stage_status
            in (
                CropStageStatus.ACTIVE,
                CropStageStatus.COMPLETED,
                CropStageStatus.SKIPPED,
            )
            else None
        ),
        completed_at=(
            date.today()
            if stage_status
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
# COMPLETE FARM HIERARCHY
# ============================================================


def create_farmer_with_farm(
    db,
    *,
    full_name="Test Farmer",
):
    user = create_user(
        db,
        full_name=full_name,
    )

    farmer = create_farmer(
        db,
        user,
    )

    farm = create_farm(
        db,
        farmer,
    )

    return user, farmer, farm


# ============================================================
# TEST CLIENT
# ============================================================


def create_client(
    db,
    user,
):
    """
    Create an authenticated TestClient.

    The real authentication dependency is overridden,
    so these router tests do not require a real JWT.
    """

    def override_db():
        yield db

    def override_current_user():
        return user

    app.dependency_overrides[get_db] = override_db

    app.dependency_overrides[get_current_user] = (
        override_current_user
    )

    return TestClient(app)


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def client(db):
    """
    Authenticated test client.

    Returns:

        client
        db
        user
        farmer
        farm
    """

    user, farmer, farm = create_farmer_with_farm(
        db,
    )

    client = create_client(
        db,
        user,
    )

    yield client, db, user, farmer, farm

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(db):
    """
    TestClient with database dependency overridden,
    but authentication dependency NOT overridden.

    Therefore requests must provide a valid authentication
    token and should receive HTTP 401 when no token exists.
    """

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


# ============================================================
# AUTHENTICATION
# ============================================================


def test_requires_authentication(
    unauthenticated_client,
):
    response = unauthenticated_client.get(
        BASE_URL,
        params={
            "crop_season_id": str(uuid4()),
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["detail"] == (
        "Invalid or expired access token."
    )


# ============================================================
# CREATE
# ============================================================


def test_create_crop_stage(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
        status=CropSeasonStatus.PLANNED,
    )

    response = client.post(
        BASE_URL,
        params={
            "crop_season_id": str(crop.id),
        },
        json={
            "name": "Land Preparation",
            "description": "Prepare the field",
            "stage_order": 1,
            "start_day": 1,
            "end_day": 5,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True

    assert body["message"] == (
        "Crop stage created successfully."
    )

    assert body["data"]["name"] == (
        "Land Preparation"
    )

    assert body["data"]["stage_order"] == 1

    assert body["data"]["status"] == "PENDING"


def test_create_stage_crop_not_found(
    client,
):
    client, db, user, farmer, farm = client

    response = client.post(
        BASE_URL,
        params={
            "crop_season_id": str(uuid4()),
        },
        json={
            "name": "Stage 1",
            "description": "Description",
            "stage_order": 1,
            "start_day": 1,
            "end_day": 5,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Crop season not found."
    )


def test_create_stage_requires_planned_crop(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
        status=CropSeasonStatus.ACTIVE,
    )

    response = client.post(
        BASE_URL,
        params={
            "crop_season_id": str(crop.id),
        },
        json={
            "name": "Stage 1",
            "description": "Description",
            "stage_order": 1,
            "start_day": 1,
            "end_day": 5,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Crop stages can only be created "
        "before farming starts."
    )


# ============================================================
# CREATE VALIDATION
# ============================================================


def test_create_stage_invalid_request(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
        status=CropSeasonStatus.PLANNED,
    )

    response = client.post(
        BASE_URL,
        params={
            "crop_season_id": str(crop.id),
        },
        json={
            "name": "",
            "description": "Description",
            "stage_order": 1,
            "start_day": 1,
            "end_day": 5,
        },
    )

    assert response.status_code == 422


# ============================================================
# OWNERSHIP
# ============================================================


def test_cannot_access_another_farmers_crop(
    client,
):
    client, db, user, farmer, farm = client

    other_user = create_user(
        db,
        full_name="Other Farmer",
    )

    other_farmer = create_farmer(
        db,
        other_user,
    )

    other_farm = create_farm(
        db,
        other_farmer,
    )

    crop = create_crop_season(
        db,
        other_farm,
    )

    response = client.get(
        BASE_URL,
        params={
            "crop_season_id": str(crop.id),
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Access denied."
    )


def test_cannot_access_another_farmers_stage(
    client,
):
    client, db, user, farmer, farm = client

    other_user = create_user(
        db,
        full_name="Other Farmer",
    )

    other_farmer = create_farmer(
        db,
        other_user,
    )

    other_farm = create_farm(
        db,
        other_farmer,
    )

    crop = create_crop_season(
        db,
        other_farm,
    )

    stage = create_stage(
        db,
        crop,
    )

    response = client.get(
        f"{BASE_URL}/{stage.id}",
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Access denied."
    )


# ============================================================
# LIST ALL
# ============================================================


def test_list_crop_stages(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    create_stage(
        db,
        crop,
        order=1,
    )

    create_stage(
        db,
        crop,
        order=2,
    )

    response = client.get(
        BASE_URL,
        params={
            "crop_season_id": str(crop.id),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["message"] == (
        "Crop stages retrieved successfully."
    )

    assert len(body["data"]) == 2

    assert body["data"][0]["stage_order"] == 1
    assert body["data"][1]["stage_order"] == 2


def test_list_crop_stages_empty(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    response = client.get(
        BASE_URL,
        params={
            "crop_season_id": str(crop.id),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"] == []


# ============================================================
# GET BY ID
# ============================================================


def test_get_crop_stage(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    stage = create_stage(
        db,
        crop,
        order=1,
    )

    response = client.get(
        f"{BASE_URL}/{stage.id}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["message"] == (
        "Crop stage retrieved successfully."
    )

    assert body["data"]["id"] == str(stage.id)

    assert body["data"]["name"] == "Stage 1"


def test_get_crop_stage_not_found(
    client,
):
    client, db, user, farmer, farm = client

    response = client.get(
        f"{BASE_URL}/{uuid4()}",
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Crop stage not found."
    )


# ============================================================
# ACTIVE
# ============================================================


def test_get_active_stage(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    stage = create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.ACTIVE,
    )

    response = client.get(
        f"{BASE_URL}/active",
        params={
            "crop_season_id": str(crop.id),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["data"]["id"] == str(stage.id)

    assert body["data"]["status"] == "ACTIVE"


def test_get_active_stage_returns_null(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    response = client.get(
        f"{BASE_URL}/active",
        params={
            "crop_season_id": str(crop.id),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"] is None


# ============================================================
# PENDING
# ============================================================


def test_get_pending_stages(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.PENDING,
    )

    create_stage(
        db,
        crop,
        order=2,
        stage_status=CropStageStatus.ACTIVE,
    )

    response = client.get(
        f"{BASE_URL}/pending",
        params={
            "crop_season_id": str(crop.id),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert len(body["data"]) == 1

    assert body["data"][0]["status"] == "PENDING"


# ============================================================
# COMPLETED
# ============================================================


def test_get_completed_stages(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.COMPLETED,
    )

    create_stage(
        db,
        crop,
        order=2,
        stage_status=CropStageStatus.PENDING,
    )

    response = client.get(
        f"{BASE_URL}/completed",
        params={
            "crop_season_id": str(crop.id),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert len(body["data"]) == 1

    assert body["data"][0]["status"] == "COMPLETED"


# ============================================================
# SKIPPED
# ============================================================


def test_get_skipped_stages(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.SKIPPED,
    )

    response = client.get(
        f"{BASE_URL}/skipped",
        params={
            "crop_season_id": str(crop.id),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert len(body["data"]) == 1

    assert body["data"][0]["status"] == "SKIPPED"


# ============================================================
# COMPLETION STATUS
# ============================================================


def test_completion_status_false_when_pending_exists(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.COMPLETED,
    )

    create_stage(
        db,
        crop,
        order=2,
        stage_status=CropStageStatus.PENDING,
    )

    response = client.get(
        f"{BASE_URL}/completion-status",
        params={
            "crop_season_id": str(crop.id),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["data"]["all_stages_finished"] is False


def test_completion_status_true_when_finished(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.COMPLETED,
    )

    create_stage(
        db,
        crop,
        order=2,
        stage_status=CropStageStatus.SKIPPED,
    )

    response = client.get(
        f"{BASE_URL}/completion-status",
        params={
            "crop_season_id": str(crop.id),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["data"]["all_stages_finished"] is True


def test_completion_status_false_when_zero_stages(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    response = client.get(
        f"{BASE_URL}/completion-status",
        params={
            "crop_season_id": str(crop.id),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["data"]["all_stages_finished"] is False


# ============================================================
# NEXT STAGE
# ============================================================


def test_get_next_stage(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    first = create_stage(
        db,
        crop,
        order=1,
    )

    second = create_stage(
        db,
        crop,
        order=2,
    )

    response = client.get(
        f"{BASE_URL}/{first.id}/next",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["data"]["id"] == str(second.id)


def test_get_next_stage_returns_null_for_final_stage(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
    )

    stage = create_stage(
        db,
        crop,
        order=1,
    )

    response = client.get(
        f"{BASE_URL}/{stage.id}/next",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["data"] is None


# ============================================================
# ACTIVATE
# ============================================================


def test_activate_stage(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
        status=CropSeasonStatus.ACTIVE,
    )

    stage = create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.PENDING,
    )

    response = client.patch(
        f"{BASE_URL}/{stage.id}/activate",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["message"] == (
        "Crop stage activated successfully."
    )

    assert body["data"]["status"] == "ACTIVE"


def test_activate_missing_stage(
    client,
):
    client, db, user, farmer, farm = client

    response = client.patch(
        f"{BASE_URL}/{uuid4()}/activate",
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Crop stage not found."
    )


# ============================================================
# COMPLETE
# ============================================================


def test_complete_stage(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
        status=CropSeasonStatus.ACTIVE,
    )

    stage = create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.ACTIVE,
    )

    response = client.patch(
        f"{BASE_URL}/{stage.id}/complete",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["message"] == (
        "Crop stage completed successfully."
    )

    assert body["data"]["status"] == "COMPLETED"


def test_complete_missing_stage(
    client,
):
    client, db, user, farmer, farm = client

    response = client.patch(
        f"{BASE_URL}/{uuid4()}/complete",
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Crop stage not found."
    )


# ============================================================
# SKIP
# ============================================================


def test_skip_stage(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
        status=CropSeasonStatus.ACTIVE,
    )

    stage = create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.ACTIVE,
    )

    response = client.patch(
        f"{BASE_URL}/{stage.id}/skip",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["message"] == (
        "Crop stage skipped successfully."
    )

    assert body["data"]["status"] == "SKIPPED"


def test_skip_missing_stage(
    client,
):
    client, db, user, farmer, farm = client

    response = client.patch(
        f"{BASE_URL}/{uuid4()}/skip",
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Crop stage not found."
    )


# ============================================================
# UPDATE
# ============================================================


def test_update_pending_stage(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
        status=CropSeasonStatus.PLANNED,
    )

    stage = create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.PENDING,
    )

    response = client.put(
        f"{BASE_URL}/{stage.id}",
        json={
            "name": "Updated Stage",
            "description": "Updated description",
            "start_day": 2,
            "end_day": 7,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["message"] == (
        "Crop stage updated successfully."
    )

    assert body["data"]["name"] == (
        "Updated Stage"
    )

    assert body["data"]["description"] == (
        "Updated description"
    )


def test_update_missing_stage(
    client,
):
    client, db, user, farmer, farm = client

    response = client.put(
        f"{BASE_URL}/{uuid4()}",
        json={
            "name": "Updated Stage",
            "description": "Updated description",
            "start_day": 2,
            "end_day": 7,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Crop stage not found."
    )


# ============================================================
# DELETE
# ============================================================


def test_delete_stage(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
        status=CropSeasonStatus.PLANNED,
    )

    stage = create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.PENDING,
    )

    stage_id = stage.id

    response = client.delete(
        f"{BASE_URL}/{stage_id}",
    )

    assert response.status_code == 204

    assert response.content == b""

    assert db.get(
        CropStage,
        stage_id,
    ) is None


def test_delete_missing_stage(
    client,
):
    client, db, user, farmer, farm = client

    response = client.delete(
        f"{BASE_URL}/{uuid4()}",
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Crop stage not found."
    )


def test_delete_active_stage_fails(
    client,
):
    client, db, user, farmer, farm = client

    crop = create_crop_season(
        db,
        farm,
        status=CropSeasonStatus.ACTIVE,
    )

    stage = create_stage(
        db,
        crop,
        order=1,
        stage_status=CropStageStatus.ACTIVE,
    )

    response = client.delete(
        f"{BASE_URL}/{stage.id}",
    )

    assert response.status_code == 400