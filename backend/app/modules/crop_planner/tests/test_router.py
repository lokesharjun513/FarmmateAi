import uuid

from datetime import date

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.database.session import get_db

from app.modules.crop_planner.router import router
from app.modules.crop_planner.service import (
    CropPlannerService,
)

from app.modules.crop_planner.schemas import (
    AIActivity,
    AICropStage,
    ActivityPriority as AIActivityPriority,
    CropPlanResponse,
)

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
    FarmingSeason,
)

from app.modules.farmer.models import Farmer
from app.modules.farm.models import Farm
from app.modules.identity.models import User

from app.shared.exceptions import ValidationError


# ============================================================
# FASTAPI APP
# ============================================================


@pytest.fixture
def app():

    app = FastAPI()

    app.include_router(
        router,
    )

    return app


# ============================================================
# USER
# ============================================================


@pytest.fixture
def current_user():

    return User(
        id=uuid.uuid4(),
    )


# ============================================================
# FARMER
# ============================================================


@pytest.fixture
def farmer(
    current_user,
):

    return Farmer(
        id=uuid.uuid4(),
        user_id=current_user.id,
    )


# ============================================================
# FARM
# ============================================================


@pytest.fixture
def farm(
    farmer,
):

    return Farm(
        id=uuid.uuid4(),
        farmer_id=farmer.id,
    )


# ============================================================
# CROP SEASON
# ============================================================


@pytest.fixture
def crop_season(
    farm,
):

    crop_season = CropSeason(

        id=uuid.uuid4(),

        farm_id=farm.id,

        crop_name="Rice",

        crop_variety="BPT 5204",

        land_area=1.0,

        land_unit="Acres",

        season=FarmingSeason.KHARIF,

        year=2026,

        sowing_date=date(
            2026,
            8,
            1,
        ),

        expected_harvest_date=None,

        harvested_date=None,

        status=CropSeasonStatus.PLANNED,

        is_active=False,

        notes=None,
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # The router accesses:
    #
    #     crop_season.farm.farmer_id
    #
    # Therefore the relationship must be explicitly attached
    # when creating the object without a database.
    # --------------------------------------------------------

    crop_season.farm = farm

    return crop_season


# ============================================================
# VALID AI CROP PLAN
# ============================================================


@pytest.fixture
def valid_plan():

    return CropPlanResponse(

        crop_name="Rice",

        crop_variety="BPT 5204",

        season="KHARIF",

        estimated_duration_days=120,

        stages=[

            # ------------------------------------------------
            # STAGE 1
            # ------------------------------------------------

            AICropStage(

                name="Land Preparation",

                description=(
                    "Prepare the field."
                ),

                stage_order=1,

                start_day=1,

                end_day=10,

                activities=[

                    AIActivity(

                        day=2,

                        title="Prepare field",

                        activity_type=(
                            "LAND_PREPARATION"
                        ),

                        description=(
                            "Prepare the field."
                        ),

                        priority=(
                            AIActivityPriority.HIGH
                        ),

                        estimated_duration_minutes=120,
                    ),

                    AIActivity(

                        day=5,

                        title="Irrigate field",

                        activity_type=(
                            "IRRIGATION"
                        ),

                        description=(
                            "Maintain soil moisture."
                        ),

                        priority=(
                            AIActivityPriority.MEDIUM
                        ),

                        estimated_duration_minutes=60,
                    ),
                ],
            ),

            # ------------------------------------------------
            # STAGE 2
            # ------------------------------------------------

            AICropStage(

                name="Sowing",

                description=(
                    "Complete rice sowing."
                ),

                stage_order=2,

                start_day=11,

                end_day=20,

                activities=[

                    AIActivity(

                        day=12,

                        title="Sow rice",

                        activity_type="SOWING",

                        description=(
                            "Sow rice seeds."
                        ),

                        priority=(
                            AIActivityPriority.HIGH
                        ),

                        estimated_duration_minutes=90,
                    ),
                ],
            ),
        ],
    )


# ============================================================
# TEST CLIENT
# ============================================================


@pytest.fixture
def client(
    app,
    current_user,
):

    def override_current_user():

        return current_user

    def override_db():

        yield None

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    app.dependency_overrides[
        get_db
    ] = override_db

    client = TestClient(
        app,
    )

    yield client

    app.dependency_overrides.clear()


# ============================================================
# FAKE FARMER REPOSITORY
# ============================================================


class FakeFarmerRepository:

    def __init__(
        self,
        farmer,
    ):

        self.farmer = farmer

    def get_by_user_id(
        self,
        user_id,
    ):

        return self.farmer


# ============================================================
# FAKE CROP SEASON REPOSITORY
# ============================================================


class FakeCropSeasonRepository:

    def __init__(
        self,
        crop_season,
    ):

        self.crop_season = crop_season

    def get_by_id(
        self,
        crop_season_id,
    ):

        return self.crop_season


# ============================================================
# FAKE CROP PLANNER REPOSITORY
# ============================================================


class FakeCropPlannerRepository:

    def __init__(
        self,
        db,
    ):

        self.db = db


# ============================================================
# PATCH REPOSITORIES
# ============================================================


@pytest.fixture
def patch_repositories(
    monkeypatch,
    farmer,
    crop_season,
):

    monkeypatch.setattr(
        "app.modules.crop_planner.router.FarmerRepository",
        lambda db: FakeFarmerRepository(
            farmer,
        ),
    )

    monkeypatch.setattr(
        "app.modules.crop_planner.router.CropSeasonRepository",
        lambda db: FakeCropSeasonRepository(
            crop_season,
        ),
    )

    monkeypatch.setattr(
        "app.modules.crop_planner.router.CropPlannerRepository",
        FakeCropPlannerRepository,
    )


# ============================================================
# VALID REQUEST
# ============================================================


def valid_request():

    return {
        "state": "Andhra Pradesh",
        "district": "Nellore",
        "village": "Sarojinidevi",
        "soil_type": "Clay",
    }


# ============================================================
# SUCCESS
# ============================================================


def test_generate_crop_plan_success(
    client,
    patch_repositories,
    valid_plan,
    monkeypatch,
):

    async def generate_plan(
        self,
        **kwargs,
    ):

        return valid_plan

    monkeypatch.setattr(
        CropPlannerService,
        "generate_plan",
        generate_plan,
    )

    crop_season_id = uuid.uuid4()

    response = client.post(
        f"/crop-planner/"
        f"{crop_season_id}/generate",
        json=valid_request(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["success"] is True

    assert data["message"] == (
        "Crop plan generated and saved successfully."
    )

    assert data["data"]["crop_name"] == "Rice"

    assert data["data"]["crop_variety"] == (
        "BPT 5204"
    )

    assert data["data"]["season"] == "KHARIF"

    assert (
        data["data"]["estimated_duration_days"]
        == 120
    )

    assert (
        data["data"]["stages_created"]
        == 2
    )

    assert (
        data["data"]["activities_created"]
        == 3
    )


# ============================================================
# REQUEST VALIDATION
# ============================================================


def test_generate_crop_plan_missing_state_fails(
    client,
    patch_repositories,
):

    request = valid_request()

    del request["state"]

    response = client.post(
        f"/crop-planner/"
        f"{uuid.uuid4()}/generate",
        json=request,
    )

    assert response.status_code == 422


def test_generate_crop_plan_missing_district_fails(
    client,
    patch_repositories,
):

    request = valid_request()

    del request["district"]

    response = client.post(
        f"/crop-planner/"
        f"{uuid.uuid4()}/generate",
        json=request,
    )

    assert response.status_code == 422


def test_generate_crop_plan_missing_village_fails(
    client,
    patch_repositories,
):

    request = valid_request()

    del request["village"]

    response = client.post(
        f"/crop-planner/"
        f"{uuid.uuid4()}/generate",
        json=request,
    )

    assert response.status_code == 422


# ============================================================
# FARMER NOT FOUND
# ============================================================


def test_generate_crop_plan_farmer_not_found(
    client,
    monkeypatch,
):

    monkeypatch.setattr(
        "app.modules.crop_planner.router.FarmerRepository",
        lambda db: FakeFarmerRepository(
            None,
        ),
    )

    response = client.post(
        f"/crop-planner/"
        f"{uuid.uuid4()}/generate",
        json=valid_request(),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Farmer profile not found."
    )


# ============================================================
# CROP SEASON NOT FOUND
# ============================================================


def test_generate_crop_plan_crop_season_not_found(
    client,
    monkeypatch,
    farmer,
):

    monkeypatch.setattr(
        "app.modules.crop_planner.router.FarmerRepository",
        lambda db: FakeFarmerRepository(
            farmer,
        ),
    )

    monkeypatch.setattr(
        "app.modules.crop_planner.router.CropSeasonRepository",
        lambda db: FakeCropSeasonRepository(
            None,
        ),
    )

    response = client.post(
        f"/crop-planner/"
        f"{uuid.uuid4()}/generate",
        json=valid_request(),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Crop season not found."
    )


# ============================================================
# ACCESS DENIED
# ============================================================


def test_generate_crop_plan_access_denied(
    client,
    monkeypatch,
    farmer,
    crop_season,
):

    # --------------------------------------------------------
    # Create a completely different farmer.
    # --------------------------------------------------------

    other_farmer = Farmer(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )

    # --------------------------------------------------------
    # Create a completely different farm belonging to the
    # other farmer.
    # --------------------------------------------------------

    other_farm = Farm(
        id=uuid.uuid4(),
        farmer_id=other_farmer.id,
    )

    # --------------------------------------------------------
    # Attach the other farm to the crop season.
    #
    # This is important because the router checks:
    #
    # crop_season.farm.farmer_id
    # --------------------------------------------------------

    crop_season.farm = other_farm

    crop_season.farm_id = (
        other_farm.id
    )

    monkeypatch.setattr(
        "app.modules.crop_planner.router.FarmerRepository",
        lambda db: FakeFarmerRepository(
            farmer,
        ),
    )

    monkeypatch.setattr(
        "app.modules.crop_planner.router.CropSeasonRepository",
        lambda db: FakeCropSeasonRepository(
            crop_season,
        ),
    )

    response = client.post(
        f"/crop-planner/"
        f"{crop_season.id}/generate",
        json=valid_request(),
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "Access denied."
    )


# ============================================================
# SERVICE VALIDATION ERROR
# ============================================================


def test_generate_crop_plan_service_validation_error(
    client,
    patch_repositories,
    monkeypatch,
):

    async def generate_plan(
        self,
        **kwargs,
    ):

        raise ValidationError(
            "A crop plan already exists for this crop season."
        )

    monkeypatch.setattr(
        CropPlannerService,
        "generate_plan",
        generate_plan,
    )

    with pytest.raises(
        ValidationError,
        match=(
            "A crop plan already exists for this crop season."
        ),
    ):

        client.post(
            f"/crop-planner/"
            f"{uuid.uuid4()}/generate",
            json=valid_request(),
        )


# ============================================================
# OPTIONAL SOIL TYPE
# ============================================================


def test_generate_crop_plan_allows_missing_soil_type(
    client,
    patch_repositories,
    valid_plan,
    monkeypatch,
):

    captured = {}

    async def generate_plan(
        self,
        **kwargs,
    ):

        captured.update(
            kwargs,
        )

        return valid_plan

    monkeypatch.setattr(
        CropPlannerService,
        "generate_plan",
        generate_plan,
    )

    request = valid_request()

    del request["soil_type"]

    response = client.post(
        f"/crop-planner/"
        f"{uuid.uuid4()}/generate",
        json=request,
    )

    assert response.status_code == 201

    assert captured["soil_type"] is None


# ============================================================
# CORRECT SERVICE PARAMETERS
# ============================================================


def test_generate_crop_plan_passes_correct_parameters(
    client,
    patch_repositories,
    valid_plan,
    crop_season,
    monkeypatch,
):

    captured = {}

    async def generate_plan(
        self,
        **kwargs,
    ):

        captured.update(
            kwargs,
        )

        return valid_plan

    monkeypatch.setattr(
        CropPlannerService,
        "generate_plan",
        generate_plan,
    )

    response = client.post(
        f"/crop-planner/"
        f"{crop_season.id}/generate",
        json=valid_request(),
    )

    assert response.status_code == 201

    assert captured["crop_season"] is (
        crop_season
    )

    assert captured["state"] == (
        "Andhra Pradesh"
    )

    assert captured["district"] == (
        "Nellore"
    )

    assert captured["village"] == (
        "Sarojinidevi"
    )

    assert captured["soil_type"] == "Clay"


# ============================================================
# RESPONSE COUNTS
# ============================================================


def test_generate_crop_plan_returns_correct_counts(
    client,
    patch_repositories,
    valid_plan,
    monkeypatch,
):

    async def generate_plan(
        self,
        **kwargs,
    ):

        return valid_plan

    monkeypatch.setattr(
        CropPlannerService,
        "generate_plan",
        generate_plan,
    )

    response = client.post(
        f"/crop-planner/"
        f"{uuid.uuid4()}/generate",
        json=valid_request(),
    )

    assert response.status_code == 201

    data = response.json()["data"]

    assert data["stages_created"] == (
        len(valid_plan.stages)
    )

    assert data["activities_created"] == (
        sum(
            len(stage.activities)
            for stage in valid_plan.stages
        )
    )


# ============================================================
# CROP SEASON ID
# ============================================================


def test_generate_crop_plan_returns_crop_season_id(
    client,
    patch_repositories,
    valid_plan,
    crop_season,
    monkeypatch,
):

    async def generate_plan(
        self,
        **kwargs,
    ):

        return valid_plan

    monkeypatch.setattr(
        CropPlannerService,
        "generate_plan",
        generate_plan,
    )

    response = client.post(
        f"/crop-planner/"
        f"{crop_season.id}/generate",
        json=valid_request(),
    )

    assert response.status_code == 201

    data = response.json()["data"]

    assert data["crop_season_id"] == (
        str(crop_season.id)
    )


# ============================================================
# METHOD NOT ALLOWED
# ============================================================


def test_generate_crop_plan_get_not_allowed(
    client,
    patch_repositories,
):

    response = client.get(
        f"/crop-planner/"
        f"{uuid.uuid4()}/generate",
    )

    assert response.status_code == 405


# ============================================================
# INVALID UUID
# ============================================================


def test_generate_crop_plan_invalid_uuid(
    client,
    patch_repositories,
):

    response = client.post(
        "/crop-planner/not-a-uuid/generate",
        json=valid_request(),
    )

    assert response.status_code == 422