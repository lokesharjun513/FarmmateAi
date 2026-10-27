from datetime import date
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.database.session import get_db
from app.modules.crop_season import router as crop_season_router
from app.modules.crop_season.models import CropSeasonStatus
from app.modules.crop_season.schemas import FarmingSeason
from app.shared.exceptions import CropSeasonNotFoundError


# ============================================================
# TEST CONSTANTS
# ============================================================

FARMER_ID = uuid4()
FARM_ID = uuid4()
CROP_SEASON_ID = uuid4()

USER_ID = uuid4()

OTHER_FARM_ID = uuid4()
OTHER_FARMER_ID = uuid4()

CROP_NAME = "Rice"


# ============================================================
# APPLICATION
# ============================================================


@pytest.fixture
def app():

    application = FastAPI()

    application.include_router(
        crop_season_router.router,
    )

    return application


# ============================================================
# TEST USER
# ============================================================


@pytest.fixture
def current_user():

    return SimpleNamespace(
        id=USER_ID,
    )


# ============================================================
# TEST FARMER
# ============================================================


@pytest.fixture
def farmer():

    return SimpleNamespace(
        id=FARMER_ID,
        user_id=USER_ID,
    )


# ============================================================
# TEST FARM
# ============================================================


@pytest.fixture
def farm():

    return SimpleNamespace(
        id=FARM_ID,
        farmer_id=FARMER_ID,
    )


# ============================================================
# TEST CROP SEASON
# ============================================================


@pytest.fixture
def crop_season(farm):

    return SimpleNamespace(
        id=CROP_SEASON_ID,
        farm_id=farm.id,

        crop_name=CROP_NAME,
        crop_variety="BPT 5204",

        season=FarmingSeason.KHARIF,
        year=2026,

        sowing_date=date(2026, 6, 15),
        expected_harvest_date=date(2026, 10, 15),
        harvested_date=None,

        land_area=1.0,
        land_unit="Acres",

        status=CropSeasonStatus.PLANNED,
        is_active=False,

        notes="Test crop",

        farm=farm,
    )


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
def client(
    app,
    current_user,
    db,
    monkeypatch,
):

    async def override_current_user():

        return current_user

    def override_db():

        return db

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    app.dependency_overrides[
        get_db
    ] = override_db

    yield TestClient(app)

    app.dependency_overrides.clear()


# ============================================================
# COMMON REPOSITORY MOCKS
# ============================================================


@pytest.fixture
def repository_mocks(
    monkeypatch,
    farmer,
    farm,
    crop_season,
):

    # --------------------------------------------------------
    # FarmerRepository
    # --------------------------------------------------------

    class FakeFarmerRepository:

        def __init__(self, db):
            self.db = db

        def get_by_user_id(self, user_id):

            if user_id == USER_ID:
                return farmer

            return None

    # --------------------------------------------------------
    # FarmRepository
    # --------------------------------------------------------

    class FakeFarmRepository:

        def __init__(self, db):
            self.db = db

        def get_by_id(self, farm_id):

            if farm_id == FARM_ID:
                return farm

            return None

    # --------------------------------------------------------
    # CropSeasonRepository
    # --------------------------------------------------------

    class FakeCropSeasonRepository:

        def __init__(self, db):
            self.db = db

    monkeypatch.setattr(
        crop_season_router,
        "FarmerRepository",
        FakeFarmerRepository,
    )

    monkeypatch.setattr(
        crop_season_router,
        "FarmRepository",
        FakeFarmRepository,
    )

    monkeypatch.setattr(
        crop_season_router,
        "CropSeasonRepository",
        FakeCropSeasonRepository,
    )


# ============================================================
# CREATE
# ============================================================


def test_create_crop_season(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    def fake_create_crop_season(
        repository,
        farm_id,
        request,
        farm=None,
    ):

        assert farm_id == FARM_ID
        assert request.crop_name == "Rice"
        assert farm.id == FARM_ID

        return crop_season

    monkeypatch.setattr(
        crop_season_router,
        "create_crop_season",
        fake_create_crop_season,
    )

    response = client.post(
        f"/crop-seasons?farm_id={FARM_ID}",
        json={
            "crop_name": "Rice",
            "crop_variety": "BPT 5204",
            "season": "KHARIF",
            "year": 2026,
            "sowing_date": "2026-06-15",
            "expected_harvest_date": "2026-10-15",
            "land_area": 1,
            "land_unit": "Acres",
            "notes": "Test crop",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Crop season created successfully."

    assert body["data"]["id"] == str(CROP_SEASON_ID)
    assert body["data"]["farm_id"] == str(FARM_ID)
    assert body["data"]["crop_name"] == "Rice"


# ============================================================
# CREATE - FARM NOT FOUND
# ============================================================


def test_create_crop_season_farm_not_found(
    client,
    repository_mocks,
):

    unknown_farm_id = uuid4()

    response = client.post(
        f"/crop-seasons?farm_id={unknown_farm_id}",
        json={
            "crop_name": "Rice",
            "season": "KHARIF",
            "year": 2026,
            "sowing_date": "2026-06-15",
            "land_area": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found."


# ============================================================
# CREATE - ACCESS DENIED
# ============================================================


def test_create_crop_season_access_denied(
    client,
    monkeypatch,
    repository_mocks,
):

    other_farm = SimpleNamespace(
        id=OTHER_FARM_ID,
        farmer_id=OTHER_FARMER_ID,
    )

    class FakeFarmRepository:

        def __init__(self, db):
            self.db = db

        def get_by_id(self, farm_id):
            return other_farm

    monkeypatch.setattr(
        crop_season_router,
        "FarmRepository",
        FakeFarmRepository,
    )

    response = client.post(
        f"/crop-seasons?farm_id={OTHER_FARM_ID}",
        json={
            "crop_name": "Rice",
            "season": "KHARIF",
            "year": 2026,
            "sowing_date": "2026-06-15",
            "land_area": 1,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied."


# ============================================================
# LIST ALL
# ============================================================


def test_list_crop_seasons(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    def fake_get_crop_seasons(
        repository,
        farm_id,
    ):

        assert farm_id == FARM_ID

        return [crop_season]

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_seasons",
        fake_get_crop_seasons,
    )

    response = client.get(
        f"/crop-seasons?farm_id={FARM_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == str(CROP_SEASON_ID)


# ============================================================
# GET ACTIVE
# ============================================================


def test_get_active_crop_season(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    crop_season.status = CropSeasonStatus.ACTIVE
    crop_season.is_active = True

    monkeypatch.setattr(
        crop_season_router,
        "get_active_crop_season",
        lambda repository, farm_id: crop_season,
    )

    response = client.get(
        f"/crop-seasons/active?farm_id={FARM_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["status"] == "ACTIVE"
    assert body["data"]["is_active"] is True


# ============================================================
# GET ACTIVE - NONE
# ============================================================


def test_get_active_crop_season_none(
    client,
    repository_mocks,
    monkeypatch,
):

    monkeypatch.setattr(
        crop_season_router,
        "get_active_crop_season",
        lambda repository, farm_id: None,
    )

    response = client.get(
        f"/crop-seasons/active?farm_id={FARM_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"] is None


# ============================================================
# GET ALL ACTIVE
# ============================================================


def test_get_active_crop_seasons(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    crop_season.status = CropSeasonStatus.ACTIVE
    crop_season.is_active = True

    monkeypatch.setattr(
        crop_season_router,
        "get_active_crop_seasons",
        lambda repository, farm_id: [crop_season],
    )

    response = client.get(
        f"/crop-seasons/active/all?farm_id={FARM_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1


# ============================================================
# GET PLANNED
# ============================================================


def test_get_planned_crop_seasons(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    monkeypatch.setattr(
        crop_season_router,
        "get_planned_crop_seasons",
        lambda repository, farm_id: [crop_season],
    )

    response = client.get(
        f"/crop-seasons/planned?farm_id={FARM_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["status"] == "PLANNED"


# ============================================================
# GET HARVESTED
# ============================================================


def test_get_harvested_crop_seasons(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    crop_season.status = CropSeasonStatus.HARVESTED
    crop_season.is_active = False
    crop_season.harvested_date = date(2026, 10, 20)

    monkeypatch.setattr(
        crop_season_router,
        "get_harvested_crop_seasons",
        lambda repository, farm_id: [crop_season],
    )

    response = client.get(
        f"/crop-seasons/harvested?farm_id={FARM_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"][0]["status"] == "HARVESTED"


# ============================================================
# GET CANCELLED
# ============================================================


def test_get_cancelled_crop_seasons(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    crop_season.status = CropSeasonStatus.CANCELLED
    crop_season.is_active = False

    monkeypatch.setattr(
        crop_season_router,
        "get_cancelled_crop_seasons",
        lambda repository, farm_id: [crop_season],
    )

    response = client.get(
        f"/crop-seasons/cancelled?farm_id={FARM_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"][0]["status"] == "CANCELLED"


# ============================================================
# GET LATEST
# ============================================================


def test_get_latest_crop_season(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    monkeypatch.setattr(
        crop_season_router,
        "get_latest_crop_season",
        lambda repository, farm_id: crop_season,
    )

    response = client.get(
        f"/crop-seasons/latest?farm_id={FARM_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == str(CROP_SEASON_ID)


# ============================================================
# GET LATEST - NONE
# ============================================================


def test_get_latest_crop_season_none(
    client,
    repository_mocks,
    monkeypatch,
):

    monkeypatch.setattr(
        crop_season_router,
        "get_latest_crop_season",
        lambda repository, farm_id: None,
    )

    response = client.get(
        f"/crop-seasons/latest?farm_id={FARM_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"] is None


# ============================================================
# GET BY ID
# ============================================================


def test_get_crop_season(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        lambda repository, crop_season_id: crop_season,
    )

    response = client.get(
        f"/crop-seasons/{CROP_SEASON_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == str(CROP_SEASON_ID)
    assert body["data"]["crop_name"] == "Rice"


# ============================================================
# GET BY ID - NOT FOUND
# ============================================================


def test_get_crop_season_not_found(
    client,
    repository_mocks,
    monkeypatch,
):

    def fake_get_crop_season(
        repository,
        crop_season_id,
    ):

        raise CropSeasonNotFoundError(
            "Crop season not found."
        )

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        fake_get_crop_season,
    )

    response = client.get(
        f"/crop-seasons/{CROP_SEASON_ID}",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop season not found."


# ============================================================
# GET BY ID - ACCESS DENIED
# ============================================================


def test_get_crop_season_access_denied(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    other_farm = SimpleNamespace(
        id=OTHER_FARM_ID,
        farmer_id=OTHER_FARMER_ID,
    )

    crop_season.farm = other_farm
    crop_season.farm_id = OTHER_FARM_ID

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        lambda repository, crop_season_id: crop_season,
    )

    response = client.get(
        f"/crop-seasons/{CROP_SEASON_ID}",
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied."


# ============================================================
# UPDATE
# ============================================================


def test_update_crop_season(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    updated_crop = crop_season
    updated_crop.crop_name = "Wheat"

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        lambda repository, crop_season_id: crop_season,
    )

    def fake_update_crop_season(
        repository,
        crop_season,
        request,
        stage_repository=None,
    ):

        assert request.crop_name == "Wheat"

        crop_season.crop_name = request.crop_name

        return crop_season

    monkeypatch.setattr(
        crop_season_router,
        "update_crop_season",
        fake_update_crop_season,
    )

    response = client.put(
        f"/crop-seasons/{CROP_SEASON_ID}",
        json={
            "crop_name": "Wheat",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["crop_name"] == "Wheat"


# ============================================================
# START FARMING
# ============================================================


def test_start_crop_season(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    crop_season.status = CropSeasonStatus.ACTIVE
    crop_season.is_active = True

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        lambda repository, crop_season_id: crop_season,
    )

    def fake_activate_crop_season(
        repository,
        stage_repository,
        crop_season,
    ):

        crop_season.status = CropSeasonStatus.ACTIVE
        crop_season.is_active = True

        return crop_season

    monkeypatch.setattr(
        crop_season_router,
        "activate_crop_season",
        fake_activate_crop_season,
    )

    response = client.patch(
        f"/crop-seasons/{CROP_SEASON_ID}/start",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Farming started successfully."
    assert body["data"]["status"] == "ACTIVE"
    assert body["data"]["is_active"] is True


# ============================================================
# COMPLETE / HARVEST
# ============================================================


def test_complete_crop_season(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    crop_season.status = CropSeasonStatus.HARVESTED
    crop_season.is_active = False
    crop_season.harvested_date = date(2026, 10, 20)

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        lambda repository, crop_season_id: crop_season,
    )

    def fake_complete_crop_season(
        repository,
        stage_repository,
        crop_season,
        request=None,
    ):

        crop_season.status = CropSeasonStatus.HARVESTED
        crop_season.is_active = False

        return crop_season

    monkeypatch.setattr(
        crop_season_router,
        "complete_crop_season",
        fake_complete_crop_season,
    )

    response = client.patch(
        f"/crop-seasons/{CROP_SEASON_ID}/complete",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert (
        body["message"]
        == "Crop season harvested successfully."
    )

    assert body["data"]["status"] == "HARVESTED"
    assert body["data"]["is_active"] is False


def test_complete_crop_season_forwards_harvest_request(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):
    captured = {}

    crop_season.status = CropSeasonStatus.HARVESTED
    crop_season.is_active = False

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        lambda repository, crop_season_id: crop_season,
    )

    def fake_complete_crop_season(
        repository,
        stage_repository,
        crop_season,
        request=None,
    ):
        captured["request"] = request

        crop_season.status = CropSeasonStatus.HARVESTED
        crop_season.is_active = False

        return crop_season

    monkeypatch.setattr(
        crop_season_router,
        "complete_crop_season",
        fake_complete_crop_season,
    )

    response = client.patch(
        f"/crop-seasons/{CROP_SEASON_ID}/complete",
        json={
            "harvested_date": "2026-09-30",
            "notes": "Harvested before rain.",
        },
    )

    assert response.status_code == 200

    request = captured["request"]

    assert request.harvested_date == date(2026, 9, 30)
    assert request.notes == "Harvested before rain."


# ============================================================
# CANCEL PLANNED
# ============================================================


def test_cancel_planned_crop(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    crop_season.status = CropSeasonStatus.CANCELLED
    crop_season.is_active = False

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        lambda repository, crop_season_id: crop_season,
    )

    def fake_cancel_crop_season(
        repository,
        crop_season,
        request=None,
        stage_repository=None,
    ):

        crop_season.status = CropSeasonStatus.CANCELLED
        crop_season.is_active = False

        return crop_season

    monkeypatch.setattr(
        crop_season_router,
        "cancel_crop_season",
        fake_cancel_crop_season,
    )

    response = client.patch(
        f"/crop-seasons/{CROP_SEASON_ID}/cancel",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert (
        body["message"]
        == "Crop season cancelled successfully."
    )

    assert body["data"]["status"] == "CANCELLED"
    assert body["data"]["is_active"] is False


# ============================================================
# CANCEL ACTIVE
# ============================================================


def test_cancel_active_crop(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    crop_season.status = CropSeasonStatus.CANCELLED
    crop_season.is_active = False

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        lambda repository, crop_season_id: crop_season,
    )

    monkeypatch.setattr(
        crop_season_router,
        "cancel_crop_season",
        lambda repository,
        crop_season,
        request=None,
        stage_repository=None: crop_season,
    )

    response = client.patch(
        f"/crop-seasons/{CROP_SEASON_ID}/cancel",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["status"] == "CANCELLED"


def test_cancel_crop_season_forwards_reason(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):
    captured = {}

    crop_season.status = CropSeasonStatus.CANCELLED
    crop_season.is_active = False
    crop_season.cancellation_reason = "Heavy rain."

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        lambda repository, crop_season_id: crop_season,
    )

    def fake_cancel_crop_season(
        repository,
        crop_season,
        request=None,
        stage_repository=None,
    ):
        captured["request"] = request
        captured["stage_repository"] = stage_repository

        crop_season.status = CropSeasonStatus.CANCELLED
        crop_season.is_active = False

        return crop_season

    monkeypatch.setattr(
        crop_season_router,
        "cancel_crop_season",
        fake_cancel_crop_season,
    )

    response = client.patch(
        f"/crop-seasons/{CROP_SEASON_ID}/cancel",
        json={
            "reason": "Heavy rain.",
        },
    )

    assert response.status_code == 200

    assert captured["request"].reason == "Heavy rain."
    assert captured["stage_repository"] is not None
    assert (
        response.json()["data"]["cancellation_reason"]
        == "Heavy rain."
    )


# ============================================================
# DELETE
# ============================================================


def test_delete_crop_season(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        lambda repository, crop_season_id: crop_season,
    )

    called = {
        "value": False,
    }

    def fake_delete_crop_season(
        repository,
        crop_season,
    ):

        called["value"] = True

    monkeypatch.setattr(
        crop_season_router,
        "delete_crop_season",
        fake_delete_crop_season,
    )

    response = client.delete(
        f"/crop-seasons/{CROP_SEASON_ID}",
    )

    assert response.status_code == 204
    assert response.content == b""
    assert called["value"] is True


# ============================================================
# DELETE - ACCESS DENIED
# ============================================================


def test_delete_crop_season_access_denied(
    client,
    repository_mocks,
    crop_season,
    monkeypatch,
):

    other_farm = SimpleNamespace(
        id=OTHER_FARM_ID,
        farmer_id=OTHER_FARMER_ID,
    )

    crop_season.farm = other_farm
    crop_season.farm_id = OTHER_FARM_ID

    monkeypatch.setattr(
        crop_season_router,
        "get_crop_season",
        lambda repository, crop_season_id: crop_season,
    )

    response = client.delete(
        f"/crop-seasons/{CROP_SEASON_ID}",
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied."


# ============================================================
# FARMER PROFILE NOT FOUND
# ============================================================


def test_farmer_profile_not_found(
    client,
    monkeypatch,
):

    class FakeFarmerRepository:

        def __init__(self, db):
            self.db = db

        def get_by_user_id(self, user_id):

            return None

    monkeypatch.setattr(
        crop_season_router,
        "FarmerRepository",
        FakeFarmerRepository,
    )

    response = client.get(
        f"/crop-seasons?farm_id={FARM_ID}",
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Farmer profile not found."
    )


# ============================================================
# FARM ACCESS CHECK
# ============================================================


def test_list_crop_seasons_farm_access_denied(
    client,
    monkeypatch,
    farmer,
):

    other_farm = SimpleNamespace(
        id=OTHER_FARM_ID,
        farmer_id=OTHER_FARMER_ID,
    )

    class FakeFarmerRepository:

        def __init__(self, db):
            self.db = db

        def get_by_user_id(self, user_id):

            return farmer

    class FakeFarmRepository:

        def __init__(self, db):
            self.db = db

        def get_by_id(self, farm_id):

            return other_farm

    monkeypatch.setattr(
        crop_season_router,
        "FarmerRepository",
        FakeFarmerRepository,
    )

    monkeypatch.setattr(
        crop_season_router,
        "FarmRepository",
        FakeFarmRepository,
    )

    response = client.get(
        f"/crop-seasons?farm_id={OTHER_FARM_ID}",
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied."


# ============================================================
# INVALID CREATE REQUEST
# ============================================================


def test_create_crop_season_invalid_request(
    client,
    repository_mocks,
):

    response = client.post(
        f"/crop-seasons?farm_id={FARM_ID}",
        json={
            "crop_name": "",
            "season": "INVALID",
            "year": 1900,
            "sowing_date": "2026-06-15",
            "land_area": 0,
        },
    )

    assert response.status_code == 422


# ============================================================
# INVALID UUID
# ============================================================


def test_get_crop_season_invalid_uuid(
    client,
    repository_mocks,
):

    response = client.get(
        "/crop-seasons/not-a-valid-uuid",
    )

    assert response.status_code == 422


# ============================================================
# ROUTE ORDER TEST
#
# Ensures /active, /planned, /latest etc. are not captured
# by /{crop_season_id}.
# ============================================================


@pytest.mark.parametrize(
    "path",
    [
        f"/crop-seasons/active?farm_id={FARM_ID}",
        f"/crop-seasons/active/all?farm_id={FARM_ID}",
        f"/crop-seasons/planned?farm_id={FARM_ID}",
        f"/crop-seasons/harvested?farm_id={FARM_ID}",
        f"/crop-seasons/cancelled?farm_id={FARM_ID}",
        f"/crop-seasons/latest?farm_id={FARM_ID}",
    ],
)
def test_static_routes_are_registered(
    client,
    repository_mocks,
    monkeypatch,
    crop_season,
    path,
):

    monkeypatch.setattr(
        crop_season_router,
        "get_active_crop_season",
        lambda repository, farm_id: None,
    )

    monkeypatch.setattr(
        crop_season_router,
        "get_active_crop_seasons",
        lambda repository, farm_id: [],
    )

    monkeypatch.setattr(
        crop_season_router,
        "get_planned_crop_seasons",
        lambda repository, farm_id: [],
    )

    monkeypatch.setattr(
        crop_season_router,
        "get_harvested_crop_seasons",
        lambda repository, farm_id: [],
    )

    monkeypatch.setattr(
        crop_season_router,
        "get_cancelled_crop_seasons",
        lambda repository, farm_id: [],
    )

    monkeypatch.setattr(
        crop_season_router,
        "get_latest_crop_season",
        lambda repository, farm_id: None,
    )

    response = client.get(path)

    assert response.status_code == 200