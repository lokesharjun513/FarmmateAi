from datetime import date
from uuid import uuid4

import pytest

from app.modules.activity.models import Activity
from app.modules.crop_planner.schemas import (
    ActivityPriority,
    AIActivity,
    AICropStage,
    CropPlanResponse,
)
from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
    FarmingSeason,
)
from app.modules.crop_stage.models import CropStage
from app.modules.farm.models import Farm
from app.modules.farmer.models import Farmer
from app.modules.farming.schemas import (
    GenerateFarmingPlanRequest,
    PlanActivity,
    PlanStage,
    StartFarmingRequest,
)
from app.modules.farming.service import FarmingService
from app.shared.exceptions import FarmNotFoundError, ValidationError


class FakePlanner:
    def __init__(self, plan: CropPlanResponse):
        self.plan = plan
        self.kwargs = None

    async def generate(self, **kwargs):
        self.kwargs = kwargs
        return self.plan


def build_plan() -> CropPlanResponse:
    return CropPlanResponse(
        crop_name="Rice",
        crop_variety="BPT 5204",
        season="KHARIF",
        estimated_duration_days=10,
        stages=[
            AICropStage(
                name="Land Preparation",
                description="Prepare the field.",
                stage_order=1,
                start_day=1,
                end_day=10,
                activities=[
                    AIActivity(
                        day=1,
                        title="Plough field",
                        activity_type="LAND_PREPARATION",
                        description="Plough the field.",
                        priority=ActivityPriority.HIGH,
                        estimated_duration_minutes=60,
                    )
                ],
            )
        ],
    )


def seed_farm(db) -> tuple[Farmer, Farm]:
    farmer = Farmer(
        id=uuid4(),
        user_id=uuid4(),
        preferred_language="English",
        experience_years=5,
        profile_completion=50,
        onboarding_completed=True,
    )
    db.add(farmer)
    db.flush()

    farm = Farm(
        id=uuid4(),
        farmer_id=farmer.id,
        farm_name="Test Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Test Village",
        land_area=5.0,
        land_unit="Acres",
        soil_type="Clay",
        is_primary=True,
    )
    db.add(farm)
    db.commit()
    db.refresh(farmer)
    db.refresh(farm)

    return farmer, farm


def plan_request(farm_id) -> GenerateFarmingPlanRequest:
    return GenerateFarmingPlanRequest(
        farm_id=farm_id,
        crop_name="Rice",
        crop_variety="BPT 5204",
        season=FarmingSeason.KHARIF,
        sowing_date=date(2026, 6, 1),
        land_area=2.0,
        land_unit="Acres",
    )


def start_request(farm_id) -> StartFarmingRequest:
    return StartFarmingRequest(
        farm_id=farm_id,
        crop_name="Rice",
        crop_variety="BPT 5204",
        season=FarmingSeason.KHARIF,
        sowing_date=date(2026, 6, 1),
        land_area=2.0,
        land_unit="Acres",
        stages=[
            PlanStage(
                name="Land Preparation",
                description="Prepare the field.",
                stage_order=1,
                start_day=1,
                end_day=10,
                activities=[
                    PlanActivity(
                        day=1,
                        title="Plough field",
                        activity_type="LAND_PREPARATION",
                        description="Plough the field.",
                        priority="HIGH",
                        estimated_duration_minutes=60,
                    )
                ],
            )
        ],
    )


@pytest.mark.asyncio
async def test_generate_plan_uses_owned_farm(db):
    farmer, farm = seed_farm(db)
    planner = FakePlanner(build_plan())
    service = FarmingService(db, planner=planner)

    response = await service.generate_plan(
        request=plan_request(farm.id),
        farmer_id=farmer.id,
    )

    assert response.crop_name == "Rice"
    assert response.season == FarmingSeason.KHARIF
    assert planner.kwargs["state"] == "Andhra Pradesh"
    assert len(response.stages) == 1


@pytest.mark.asyncio
async def test_generate_plan_rejects_another_farmers_farm(db):
    _, farm = seed_farm(db)
    service = FarmingService(db, planner=FakePlanner(build_plan()))

    with pytest.raises(FarmNotFoundError):
        await service.generate_plan(
            request=plan_request(farm.id),
            farmer_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_start_farming_persists_owned_crop(db):
    farmer, farm = seed_farm(db)
    service = FarmingService(db)

    response = await service.start_farming(
        request=start_request(farm.id),
        farmer_id=farmer.id,
    )

    assert response.total_stages == 1
    assert response.total_activities == 1
    assert response.estimated_duration_days == 10

    crop = db.query(CropSeason).filter(CropSeason.id == response.crop_season_id).one()
    assert crop.farm_id == farm.id
    assert crop.expected_harvest_date == date(2026, 6, 10)

    stage = db.query(CropStage).one()
    assert stage.status.value == "ACTIVE"
    assert stage.started_at == date(2026, 6, 1)

    assert db.query(Activity).count() == 1


@pytest.mark.asyncio
async def test_start_farming_rejects_when_farm_has_active_crop(db):
    farmer, farm = seed_farm(db)
    service = FarmingService(db)

    active_crop = CropSeason(
        farm_id=farm.id,
        crop_name="Rice",
        crop_variety="BPT 5204",
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 1),
        expected_harvest_date=date(2026, 10, 1),
        land_area=2.0,
        land_unit="Acres",
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )
    db.add(active_crop)
    db.commit()

    with pytest.raises(
        ValidationError,
        match="already active",
    ):
        await service.start_farming(
            request=start_request(farm.id),
            farmer_id=farmer.id,
        )

    assert db.query(CropSeason).count() == 1


@pytest.mark.asyncio
async def test_start_farming_rejects_another_farmers_farm(db):
    _, farm = seed_farm(db)
    service = FarmingService(db)

    with pytest.raises(FarmNotFoundError):
        await service.start_farming(
            request=start_request(farm.id),
            farmer_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_start_farming_rejects_invalid_stage_order(db):
    farmer, farm = seed_farm(db)
    service = FarmingService(db)
    request = start_request(farm.id)
    request.stages[0].stage_order = 2

    with pytest.raises(Exception, match="sequential"):
        await service.start_farming(
            request=request,
            farmer_id=farmer.id,
        )
