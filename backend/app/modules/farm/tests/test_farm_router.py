# app/modules/farm/tests/test_farm_router.py

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.database.session import get_db
from app.main import app

from app.modules.farm.models import Farm
from app.modules.farmer.repository import FarmerRepository


# ============================================================
# CONSTANTS
# ============================================================

FARMS_URL = "/api/v1/farms"


# ============================================================
# TEST USER / FARMER
# ============================================================

TEST_USER_ID = uuid4()
TEST_FARMER_ID = uuid4()


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def current_user_id():
    """
    Fake authenticated user ID used by router tests.
    """
    return TEST_USER_ID


@pytest.fixture
def client(
    db,
    current_user_id,
    monkeypatch,
):
    """
    Create a FastAPI TestClient with:

    - fake authenticated user
    - test database
    - fake farmer profile

    We mock FarmerRepository.get_by_user_id because these
    router tests are focused on the Farm module, not the
    Farmer module.
    """

    fake_user = SimpleNamespace(
        id=current_user_id,
    )

    fake_farmer = SimpleNamespace(
        id=TEST_FARMER_ID,
        user_id=current_user_id,
    )

    # --------------------------------------------------------
    # Authentication override
    # --------------------------------------------------------

    app.dependency_overrides[
        get_current_user
    ] = lambda: fake_user

    # --------------------------------------------------------
    # Database override
    # --------------------------------------------------------

    app.dependency_overrides[
        get_db
    ] = lambda: db

    # --------------------------------------------------------
    # Farmer repository override
    #
    # Every request from the fake authenticated user receives
    # the same farmer profile.
    # --------------------------------------------------------

    monkeypatch.setattr(
        FarmerRepository,
        "get_by_user_id",
        lambda self, user_id: (
            fake_farmer
            if user_id == current_user_id
            else None
        ),
    )

    try:
        with TestClient(app) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.clear()


# ============================================================
# HELPERS
# ============================================================


def farm_payload(
    farm_name: str = "My Farm",
    land_area: float = 2.5,
    latitude: float | None = 14.9167,
    longitude: float | None = 79.9944,
    is_primary: bool = False,
):
    return {
        "farm_name": farm_name,
        "state": "Andhra Pradesh",
        "district": "Nellore",
        "mandal": "Kavali",
        "village": "Example Village",
        "latitude": latitude,
        "longitude": longitude,
        "land_area": land_area,
        "land_unit": "Acres",
        "soil_type": "Clay",
        "water_source": "Borewell",
        "water_availability": "HIGH",
        "irrigation_method": "Drip",
        "is_primary": is_primary,
    }


def create_farm_in_db(
    db,
    farmer_id: UUID | None = None,
    farm_name: str = "Test Farm",
    is_primary: bool = False,
):
    """
    Create a Farm directly in the test database.
    """

    if farmer_id is None:
        farmer_id = TEST_FARMER_ID

    farm = Farm(
        farmer_id=farmer_id,
        farm_name=farm_name,
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Example Village",
        latitude=14.9167,
        longitude=79.9944,
        land_area=2.5,
        land_unit="Acres",
        soil_type="Clay",
        water_source="Borewell",
        water_availability="HIGH",
        irrigation_method="Drip",
        is_primary=is_primary,
    )

    db.add(farm)
    db.commit()
    db.refresh(farm)

    return farm


# ============================================================
# CREATE FARM
# ============================================================


def test_create_farm(
    client,
):
    response = client.post(
        FARMS_URL,
        json=farm_payload(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Farm created successfully."
    assert body["errors"] == []

    assert body["data"]["farm_name"] == "My Farm"
    assert body["data"]["state"] == "Andhra Pradesh"
    assert body["data"]["district"] == "Nellore"
    assert body["data"]["mandal"] == "Kavali"
    assert body["data"]["village"] == "Example Village"

    assert body["data"]["land_area"] == 2.5
    assert body["data"]["land_unit"] == "Acres"

    assert body["data"]["is_primary"] is False


def test_create_primary_farm(
    client,
):
    response = client.post(
        FARMS_URL,
        json=farm_payload(
            farm_name="Primary Farm",
            is_primary=True,
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Farm created successfully."

    assert body["data"]["farm_name"] == "Primary Farm"
    assert body["data"]["is_primary"] is True


# ============================================================
# GET ALL FARMS
# ============================================================


def test_get_all_farms(
    client,
):
    response = client.get(
        FARMS_URL,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Farms retrieved successfully."
    assert body["errors"] == []

    assert isinstance(
        body["data"],
        list,
    )


# ============================================================
# GET FARM
# ============================================================


def test_get_farm(
    client,
    db,
):
    farm = create_farm_in_db(
        db,
        farm_name="My Farm",
    )

    response = client.get(
        f"{FARMS_URL}/{farm.id}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Farm retrieved successfully."

    assert body["data"]["id"] == str(farm.id)
    assert body["data"]["farm_name"] == "My Farm"


def test_get_farm_not_found(
    client,
):
    farm_id = uuid4()

    response = client.get(
        f"{FARMS_URL}/{farm_id}",
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Farm not found."
    assert body["errors"] == []


def test_get_farm_wrong_farmer(
    client,
    db,
):
    other_farmer_id = uuid4()

    farm = create_farm_in_db(
        db,
        farmer_id=other_farmer_id,
        farm_name="Other Farmer Farm",
    )

    response = client.get(
        f"{FARMS_URL}/{farm.id}",
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Farm not found."
    assert body["errors"] == []


# ============================================================
# UPDATE FARM
# ============================================================


def test_update_farm(
    client,
    db,
):
    farm = create_farm_in_db(
        db,
        farm_name="Old Farm Name",
    )

    response = client.patch(
        f"{FARMS_URL}/{farm.id}",
        json={
            "farm_name": "Updated Farm Name",
            "land_area": 5.0,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Farm updated successfully."

    assert body["data"]["id"] == str(farm.id)
    assert body["data"]["farm_name"] == "Updated Farm Name"
    assert body["data"]["land_area"] == 5.0


def test_update_farm_switches_primary(
    client,
    db,
):
    first = create_farm_in_db(
        db,
        farm_name="First Farm",
        is_primary=True,
    )

    second = create_farm_in_db(
        db,
        farm_name="Second Farm",
        is_primary=False,
    )

    response = client.patch(
        f"{FARMS_URL}/{second.id}",
        json={
            "is_primary": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["data"]["id"] == str(second.id)
    assert body["data"]["is_primary"] is True

    db.expire_all()

    farms = (
        db.query(Farm)
        .filter(
            Farm.farmer_id == TEST_FARMER_ID,
        )
        .all()
    )

    primary_farms = [
        farm
        for farm in farms
        if farm.is_primary
    ]

    assert len(primary_farms) == 1
    assert primary_farms[0].id == second.id

    first = (
        db.query(Farm)
        .filter(
            Farm.id == first.id,
        )
        .one()
    )

    assert first.is_primary is False


def test_update_current_primary_farm_is_idempotent(
    client,
    db,
):
    first = create_farm_in_db(
        db,
        farm_name="First Farm",
        is_primary=True,
    )

    create_farm_in_db(
        db,
        farm_name="Second Farm",
        is_primary=False,
    )

    response = client.patch(
        f"{FARMS_URL}/{first.id}",
        json={
            "is_primary": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["is_primary"] is True

    db.expire_all()

    primary_farms = (
        db.query(Farm)
        .filter(
            Farm.farmer_id == TEST_FARMER_ID,
            Farm.is_primary.is_(True),
        )
        .all()
    )

    assert len(primary_farms) == 1
    assert primary_farms[0].id == first.id


def test_update_farm_not_found(
    client,
):
    response = client.patch(
        f"{FARMS_URL}/{uuid4()}",
        json={
            "is_primary": True,
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Farm not found."


def test_update_farm_rejects_invalid_primary_value(
    client,
    db,
):
    farm = create_farm_in_db(
        db,
        farm_name="Test Farm",
    )

    response = client.patch(
        f"{FARMS_URL}/{farm.id}",
        json={
            "is_primary": "not-a-boolean",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body


def test_update_farm_wrong_farmer(
    client,
    db,
):
    other_farmer_id = uuid4()

    farm = create_farm_in_db(
        db,
        farmer_id=other_farmer_id,
        farm_name="Other Farmer Farm",
    )

    response = client.patch(
        f"{FARMS_URL}/{farm.id}",
        json={
            "farm_name": "Hacked Farm",
        },
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Farm not found."
    assert body["errors"] == []


# ============================================================
# DELETE FARM
# ============================================================


def test_delete_farm(
    client,
    db,
):
    farm = create_farm_in_db(
        db,
        farm_name="Farm To Delete",
    )

    farm_id = farm.id

    response = client.delete(
        f"{FARMS_URL}/{farm_id}",
    )

    assert response.status_code == 204

    deleted_farm = (
        db.query(Farm)
        .filter(
            Farm.id == farm_id,
        )
        .first()
    )

    assert deleted_farm is None


def test_delete_farm_wrong_farmer(
    client,
    db,
):
    other_farmer_id = uuid4()

    farm = create_farm_in_db(
        db,
        farmer_id=other_farmer_id,
        farm_name="Other Farmer Farm",
    )

    farm_id = farm.id

    response = client.delete(
        f"{FARMS_URL}/{farm_id}",
    )

    assert response.status_code == 404

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Farm not found."
    assert body["errors"] == []

    # --------------------------------------------------------
    # Make sure another farmer's farm was NOT deleted.
    # --------------------------------------------------------

    existing_farm = (
        db.query(Farm)
        .filter(
            Farm.id == farm_id,
        )
        .first()
    )

    assert existing_farm is not None


# ============================================================
# VALIDATION
# ============================================================


def test_create_farm_rejects_invalid_land_area(
    client,
):
    response = client.post(
        FARMS_URL,
        json=farm_payload(
            land_area=0,
        ),
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body


def test_create_farm_rejects_invalid_latitude(
    client,
):
    response = client.post(
        FARMS_URL,
        json=farm_payload(
            latitude=90.1,
        ),
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body


def test_create_farm_rejects_invalid_longitude(
    client,
):
    response = client.post(
        FARMS_URL,
        json=farm_payload(
            longitude=180.1,
        ),
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body


# ============================================================
# FARMER PROFILE NOT FOUND
# ============================================================


def test_create_farm_without_farmer_profile(
    db,
    current_user_id,
    monkeypatch,
):
    fake_user = SimpleNamespace(
        id=current_user_id,
    )

    app.dependency_overrides[
        get_current_user
    ] = lambda: fake_user

    app.dependency_overrides[
        get_db
    ] = lambda: db

    # --------------------------------------------------------
    # Simulate missing farmer profile.
    # --------------------------------------------------------

    monkeypatch.setattr(
        FarmerRepository,
        "get_by_user_id",
        lambda self, user_id: None,
    )

    try:
        with TestClient(app) as client:

            response = client.post(
                FARMS_URL,
                json=farm_payload(),
            )

        assert response.status_code == 404

        body = response.json()

        assert body["success"] is False
        assert body["message"] == "Farmer profile not found."
        assert body["errors"] == []

    finally:
        app.dependency_overrides.clear()


def test_get_all_farms_without_farmer_profile(
    db,
    current_user_id,
    monkeypatch,
):
    fake_user = SimpleNamespace(
        id=current_user_id,
    )

    app.dependency_overrides[
        get_current_user
    ] = lambda: fake_user

    app.dependency_overrides[
        get_db
    ] = lambda: db

    # --------------------------------------------------------
    # Simulate missing farmer profile.
    # --------------------------------------------------------

    monkeypatch.setattr(
        FarmerRepository,
        "get_by_user_id",
        lambda self, user_id: None,
    )

    try:
        with TestClient(app) as client:

            response = client.get(
                FARMS_URL,
            )

        assert response.status_code == 404

        body = response.json()

        assert body["success"] is False
        assert body["message"] == "Farmer profile not found."
        assert body["errors"] == []

    finally:
        app.dependency_overrides.clear()