from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.database.session import get_db

from app.modules.activity.models import (
    Activity,
    ActivityPriority,
    ActivitySource,
    ActivityStatus,
    ActivityType,
)

from app.modules.activity.router import router

from app.modules.farmer.repository import (
    FarmerRepository,
)

from app.modules.crop_season.repository import (
    CropSeasonRepository,
)

from app.modules.crop_stage.repository import (
    CropStageRepository,
)

from app.modules.activity.repository import (
    ActivityRepository,
)

from app.modules.identity.models import User


# ============================================================
# TEST APP
# ============================================================

app = FastAPI()

app.include_router(router)


# ============================================================
# TEST IDS
# ============================================================

USER_ID = uuid4()
FARMER_ID = uuid4()
FARM_ID = uuid4()
CROP_SEASON_ID = uuid4()
OTHER_CROP_SEASON_ID = uuid4()
STAGE_ID = uuid4()
OTHER_STAGE_ID = uuid4()
ACTIVITY_ID = uuid4()
OTHER_ACTIVITY_ID = uuid4()


# ============================================================
# MOCK USER
# ============================================================


@pytest.fixture
def mock_user():

    user = SimpleNamespace(
        id=USER_ID,
    )

    return user


# ============================================================
# MOCK FARMER
# ============================================================


@pytest.fixture
def mock_farmer():

    farmer = SimpleNamespace(
        id=FARMER_ID,
        user_id=USER_ID,
    )

    return farmer


# ============================================================
# MOCK CROP SEASON
# ============================================================


@pytest.fixture
def mock_crop():

    farm = SimpleNamespace(
        farmer_id=FARMER_ID,
    )

    crop = SimpleNamespace(
        id=CROP_SEASON_ID,
        farm=farm,
        status=SimpleNamespace(
            value="ACTIVE",
        ),
    )

    return crop


# ============================================================
# MOCK STAGE
# ============================================================


@pytest.fixture
def mock_stage(mock_crop):

    stage = SimpleNamespace(
        id=STAGE_ID,
        crop_season_id=CROP_SEASON_ID,
        crop_season=mock_crop,
    )

    return stage


# ============================================================
# MOCK ACTIVITY
# ============================================================


@pytest.fixture
def mock_activity(mock_crop):

    activity = SimpleNamespace(
        id=ACTIVITY_ID,
        crop_season_id=CROP_SEASON_ID,
        stage_id=STAGE_ID,
        activity_type=ActivityType.IRRIGATION,
        title="Irrigate field",
        description="Irrigate the crop field.",
        scheduled_date=date.today(),
        original_scheduled_date=None,
        completed_date=None,
        status=ActivityStatus.PENDING,
        notes=None,
        priority=ActivityPriority.MEDIUM,
        estimated_duration_minutes=30,
        source=ActivitySource.AI_PLANNED,
        crop_season=mock_crop,
    )

    return activity


# ============================================================
# TEST DATABASE
# ============================================================


@pytest.fixture
def db():

    return SimpleNamespace()


# ============================================================
# CLIENT
# ============================================================


@pytest.fixture
def client(mock_user, db):

    def override_current_user():

        return mock_user

    def override_db():

        yield db

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    app.dependency_overrides[
        get_db
    ] = override_db

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


# ============================================================
# FARMER REPOSITORY MOCK
# ============================================================


@pytest.fixture
def farmer_repository(
    monkeypatch,
    mock_farmer,
):

    repository = __import__(
        "app.modules.activity.router",
        fromlist=["FarmerRepository"],
    ).FarmerRepository

    mock = repository

    monkeypatch.setattr(
        mock,
        "get_by_user_id",
        lambda self, user_id: mock_farmer,
    )

    return mock


# ============================================================
# HELPER:
# MOCK FARMER REPOSITORY
# ============================================================


def patch_farmer(
    monkeypatch,
    mock_farmer,
):

    repository = __import__(
        "app.modules.activity.router",
        fromlist=["FarmerRepository"],
    ).FarmerRepository

    monkeypatch.setattr(
        repository,
        "get_by_user_id",
        lambda self, user_id: mock_farmer,
    )


# ============================================================
# HELPER:
# MOCK CROP REPOSITORY
# ============================================================


def patch_crop(
    monkeypatch,
    crop,
):

    repository = __import__(
        "app.modules.activity.router",
        fromlist=["CropSeasonRepository"],
    ).CropSeasonRepository

    monkeypatch.setattr(
        repository,
        "get_by_id",
        lambda self, crop_id: crop,
    )


# ============================================================
# HELPER:
# MOCK STAGE REPOSITORY
# ============================================================


def patch_stage(
    monkeypatch,
    stage,
):

    repository = __import__(
        "app.modules.activity.router",
        fromlist=["CropStageRepository"],
    ).CropStageRepository

    monkeypatch.setattr(
        repository,
        "get_by_id",
        lambda self, stage_id: stage,
    )


# ============================================================
# HELPER:
# MOCK ACTIVITY REPOSITORY
# ============================================================


def patch_activity(
    monkeypatch,
    activity,
):

    repository = __import__(
        "app.modules.activity.router",
        fromlist=["ActivityRepository"],
    ).ActivityRepository

    monkeypatch.setattr(
        repository,
        "get_by_id",
        lambda self, activity_id: activity,
    )


# ============================================================
# CREATE ACTIVITY
# ============================================================


def test_create_activity(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    created_activity = SimpleNamespace(
        id=ACTIVITY_ID,
        crop_season_id=CROP_SEASON_ID,
        stage_id=None,
        activity_type=ActivityType.IRRIGATION,
        title="Irrigate field",
        description="Irrigate the crop field.",
        scheduled_date=date.today(),
        original_scheduled_date=None,
        completed_date=None,
        status=ActivityStatus.PENDING,
        notes=None,
        priority=ActivityPriority.MEDIUM,
        estimated_duration_minutes=30,
        source=ActivitySource.FARMER_ADDED,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.create_activity",
        lambda repository, crop_season_id, request:
            created_activity,
    )

    response = client.post(
        f"/activities?crop_season_id={CROP_SEASON_ID}",
        json={
            "activity_type": "IRRIGATION",
            "title": "Irrigate field",
            "description": "Irrigate the crop field.",
            "scheduled_date": str(date.today()),
            "priority": "MEDIUM",
            "estimated_duration_minutes": 30,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True

    assert body["message"] == (
        "Activity created successfully."
    )


# ============================================================
# CREATE ACTIVITY:
# CROP NOT FOUND
# ============================================================


def test_create_activity_crop_not_found(
    client,
    monkeypatch,
    mock_farmer,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    repository = __import__(
        "app.modules.activity.router",
        fromlist=["CropSeasonRepository"],
    ).CropSeasonRepository

    monkeypatch.setattr(
        repository,
        "get_by_id",
        lambda self, crop_id: None,
    )

    response = client.post(
        f"/activities?crop_season_id={CROP_SEASON_ID}",
        json={
            "activity_type": "IRRIGATION",
            "title": "Irrigate field",
            "scheduled_date": str(date.today()),
            "priority": "MEDIUM",
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Crop season not found."
    )


# ============================================================
# CREATE ACTIVITY:
# ACCESS DENIED
# ============================================================


def test_create_activity_access_denied(
    client,
    monkeypatch,
    mock_crop,
):

    other_farmer = SimpleNamespace(
        id=uuid4(),
        user_id=USER_ID,
    )

    patch_farmer(
        monkeypatch,
        other_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    response = client.post(
        f"/activities?crop_season_id={CROP_SEASON_ID}",
        json={
            "activity_type": "IRRIGATION",
            "title": "Irrigate field",
            "scheduled_date": str(date.today()),
            "priority": "MEDIUM",
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Access denied."
    )


# ============================================================
# CREATE ACTIVITY:
# HARVESTED CROP
# ============================================================


def test_create_activity_harvested_crop(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    mock_crop.status = SimpleNamespace(
        value="HARVESTED",
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    response = client.post(
        f"/activities?crop_season_id={CROP_SEASON_ID}",
        json={
            "activity_type": "IRRIGATION",
            "title": "Irrigate field",
            "scheduled_date": str(date.today()),
            "priority": "MEDIUM",
        },
    )

    assert response.status_code == 400

    assert (
        "harvested or cancelled"
        in response.json()["detail"]
    )


# ============================================================
# LIST ACTIVITIES
# ============================================================


def test_list_activities(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_crop_activities",
        lambda repository, crop_season_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert len(body["data"]) == 1

    assert body["data"][0]["title"] == (
        "Irrigate field"
    )


# ============================================================
# TODAY
# ============================================================


def test_today_activities(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_today_activities",
        lambda repository, crop_season_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities/today?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200

    assert len(
        response.json()["data"]
    ) == 1


# ============================================================
# TODAY PENDING
# ============================================================


def test_today_pending_activities(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_today_pending_activities",
        lambda repository, crop_season_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities/today/pending"
        f"?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# TODAY IN-PROGRESS
# ============================================================


def test_today_in_progress_activities(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_today_in_progress_activities",
        lambda repository, crop_season_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities/today/in-progress"
        f"?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# TODAY COMPLETED
# ============================================================


def test_today_completed_activities(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_today_completed_activities",
        lambda repository, crop_season_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities/today/completed"
        f"?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# PENDING
# ============================================================


def test_pending_activities(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_pending_activities",
        lambda repository, crop_season_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities/pending?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# UPCOMING
# ============================================================


def test_upcoming_activities(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_upcoming_activities",
        lambda repository, crop_season_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities/upcoming?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# OVERDUE
# ============================================================


def test_overdue_activities(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_overdue_activities",
        lambda repository, crop_season_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities/overdue?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# IN-PROGRESS
# ============================================================


def test_in_progress_activities(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_in_progress_activities",
        lambda repository, crop_season_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities/in-progress"
        f"?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# COMPLETED
# ============================================================


def test_completed_activities(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_completed_activities",
        lambda repository, crop_season_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities/completed"
        f"?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# SKIPPED
# ============================================================


def test_skipped_activities(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_skipped_activities",
        lambda repository, crop_season_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities/skipped"
        f"?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# BY STATUS
# ============================================================


def test_activities_by_status(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_activities_by_status",
        lambda repository, crop_season_id, activity_status:
            [mock_activity],
    )

    response = client.get(
        f"/activities/status/PENDING"
        f"?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# BY SOURCE
# ============================================================


def test_activities_by_source(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_activities_by_source",
        lambda repository, crop_season_id, source:
            [mock_activity],
    )

    response = client.get(
        f"/activities/source/AI_PLANNED"
        f"?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# BY PRIORITY
# ============================================================


def test_activities_by_priority(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_activities_by_priority",
        lambda repository, crop_season_id, priority:
            [mock_activity],
    )

    response = client.get(
        f"/activities/priority/HIGH"
        f"?crop_season_id={CROP_SEASON_ID}",
    )

    assert response.status_code == 200


# ============================================================
# DATE RANGE
# ============================================================


def test_activities_by_date_range(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_activities_by_date_range",
        lambda repository,
        crop_season_id,
        start_date,
        end_date:
            [mock_activity],
    )

    response = client.get(
        "/activities/date-range"
        f"?crop_season_id={CROP_SEASON_ID}"
        "&start_date=2026-08-01"
        "&end_date=2026-08-15",
    )

    assert response.status_code == 200


# ============================================================
# INVALID DATE RANGE
# ============================================================


def test_invalid_date_range(
    client,
    monkeypatch,
    mock_farmer,
    mock_crop,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_crop(
        monkeypatch,
        mock_crop,
    )

    response = client.get(
        "/activities/date-range"
        f"?crop_season_id={CROP_SEASON_ID}"
        "&start_date=2026-08-15"
        "&end_date=2026-08-01",
    )

    assert response.status_code == 400

    assert (
        "End date must be greater than or equal"
        in response.json()["detail"]
    )


# ============================================================
# BY STAGE
# ============================================================


def test_activities_by_stage(
    client,
    monkeypatch,
    mock_farmer,
    mock_stage,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_stage(
        monkeypatch,
        mock_stage,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.get_stage_activities",
        lambda repository, stage_id:
            [mock_activity],
    )

    response = client.get(
        f"/activities/stage/{STAGE_ID}",
    )

    assert response.status_code == 200


# ============================================================
# GET BY ID
# ============================================================


def test_get_activity(
    client,
    monkeypatch,
    mock_farmer,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_activity(
        monkeypatch,
        mock_activity,
    )

    response = client.get(
        f"/activities/{ACTIVITY_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["data"]["title"] == (
        "Irrigate field"
    )


# ============================================================
# GET BY ID NOT FOUND
# ============================================================


def test_get_activity_not_found(
    client,
    monkeypatch,
    mock_farmer,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    repository = __import__(
        "app.modules.activity.router",
        fromlist=["ActivityRepository"],
    ).ActivityRepository

    monkeypatch.setattr(
        repository,
        "get_by_id",
        lambda self, activity_id: None,
    )

    response = client.get(
        f"/activities/{ACTIVITY_ID}",
    )

    assert response.status_code == 404


# ============================================================
# UPDATE ACTIVITY
# ============================================================


def test_update_activity(
    client,
    monkeypatch,
    mock_farmer,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_activity(
        monkeypatch,
        mock_activity,
    )

    updated_activity = mock_activity

    updated_activity.title = (
        "Updated irrigation"
    )

    monkeypatch.setattr(
        "app.modules.activity.router.update_activity",
        lambda repository, activity, request:
            updated_activity,
    )

    response = client.put(
        f"/activities/{ACTIVITY_ID}",
        json={
            "title": "Updated irrigation",
        },
    )

    assert response.status_code == 200

    assert response.json()["success"] is True


# ============================================================
# START ACTIVITY
# ============================================================


def test_start_activity(
    client,
    monkeypatch,
    mock_farmer,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_activity(
        monkeypatch,
        mock_activity,
    )

    started_activity = mock_activity
    started_activity.status = (
        ActivityStatus.IN_PROGRESS
    )

    monkeypatch.setattr(
        "app.modules.activity.router.start_activity",
        lambda repository, activity:
            started_activity,
    )

    response = client.patch(
        f"/activities/{ACTIVITY_ID}/start",
    )

    assert response.status_code == 200

    assert response.json()["success"] is True


# ============================================================
# COMPLETE ACTIVITY
# ============================================================


def test_complete_activity(
    client,
    monkeypatch,
    mock_farmer,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    mock_activity.status = (
        ActivityStatus.IN_PROGRESS
    )

    patch_activity(
        monkeypatch,
        mock_activity,
    )

    completed_activity = mock_activity
    completed_activity.status = (
        ActivityStatus.COMPLETED
    )
    completed_activity.completed_date = date.today()

    monkeypatch.setattr(
        "app.modules.activity.router.complete_activity",
        lambda repository, activity:
            completed_activity,
    )

    response = client.patch(
        f"/activities/{ACTIVITY_ID}/complete",
    )

    assert response.status_code == 200

    assert response.json()["success"] is True


# ============================================================
# SKIP ACTIVITY
# ============================================================


def test_skip_activity(
    client,
    monkeypatch,
    mock_farmer,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_activity(
        monkeypatch,
        mock_activity,
    )

    skipped_activity = mock_activity
    skipped_activity.status = (
        ActivityStatus.SKIPPED
    )

    monkeypatch.setattr(
        "app.modules.activity.router.skip_activity",
        lambda repository, activity:
            skipped_activity,
    )

    response = client.patch(
        f"/activities/{ACTIVITY_ID}/skip",
    )

    assert response.status_code == 200

    assert response.json()["success"] is True


# ============================================================
# DELETE ACTIVITY
# ============================================================


def test_delete_activity(
    client,
    monkeypatch,
    mock_farmer,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    patch_activity(
        monkeypatch,
        mock_activity,
    )

    monkeypatch.setattr(
        "app.modules.activity.router.delete_activity",
        lambda repository, activity:
            None,
    )

    response = client.delete(
        f"/activities/{ACTIVITY_ID}",
    )

    assert response.status_code == 204


# ============================================================
# UPDATE FINISHED CROP
# ============================================================


def test_update_activity_finished_crop(
    client,
    monkeypatch,
    mock_farmer,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    mock_activity.crop_season.status = (
        SimpleNamespace(
            value="HARVESTED",
        )
    )

    patch_activity(
        monkeypatch,
        mock_activity,
    )

    response = client.put(
        f"/activities/{ACTIVITY_ID}",
        json={
            "title": "Updated irrigation",
        },
    )

    assert response.status_code == 400

    assert (
        "crop season has ended"
        in response.json()["detail"]
    )


# ============================================================
# DELETE FINISHED CROP
# ============================================================


def test_delete_activity_finished_crop(
    client,
    monkeypatch,
    mock_farmer,
    mock_activity,
):

    patch_farmer(
        monkeypatch,
        mock_farmer,
    )

    mock_activity.crop_season.status = (
        SimpleNamespace(
            value="HARVESTED",
        )
    )

    patch_activity(
        monkeypatch,
        mock_activity,
    )

    response = client.delete(
        f"/activities/{ACTIVITY_ID}",
    )

    assert response.status_code == 400

    assert (
        "crop season has ended"
        in response.json()["detail"]
    )