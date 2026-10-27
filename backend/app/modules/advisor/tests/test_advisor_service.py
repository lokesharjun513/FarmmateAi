from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.modules.advisor.schemas import (
    AdvicePriority,
    DailyAdvisorResponse,
)
from app.modules.advisor.service import AdvisorService
from app.modules.ai_engine.context import AIContext
from app.shared.exceptions import ValidationError


# ============================================================
# TEST IDS
# ============================================================

FARMER_ID = uuid4()
FARM_ID = uuid4()
CROP_ID = uuid4()


# ============================================================
# HELPERS
# ============================================================


def create_farmer():

    return SimpleNamespace(
        id=FARMER_ID,
    )


def create_farm(
    *,
    is_primary=True,
    latitude=14.4426,
    longitude=79.9865,
):

    return SimpleNamespace(
        id=FARM_ID,
        farmer_id=FARMER_ID,
        is_primary=is_primary,
        latitude=latitude,
        longitude=longitude,
        village="Kavali",
        district="Nellore",
        soil_type="Clay Loam",
    )


def create_crop(
    *,
    sowing_date=None,
):

    if sowing_date is None:
        sowing_date = date.today() - timedelta(
            days=45,
        )

    return SimpleNamespace(
        id=CROP_ID,
        farm_id=FARM_ID,
        crop_name="Rice",
        crop_variety="BPT 5204",
        sowing_date=sowing_date,
    )


def create_activity(
    title="Irrigate field",
):

    return SimpleNamespace(
        id=uuid4(),
        title=title,
    )


def create_weather():

    return SimpleNamespace(
        weather_condition="Clear Sky",
        temperature=32.5,
        humidity=70,
        rain_probability=20,
    )


def create_advice():

    return DailyAdvisorResponse(
        summary=(
            "Conditions are suitable for normal "
            "farm activities today."
        ),
        warnings=[
            "Monitor soil moisture before irrigation.",
        ],
        recommendations=[
            "Check field moisture.",
            "Complete planned irrigation if required.",
            "Monitor the crop for pests.",
        ],
        priority=AdvicePriority.LOW,
    )


# ============================================================
# MOCK REPOSITORIES
# ============================================================


class MockFarmRepository:

    def __init__(self, farms=None):

        self.farms = farms or []

    def get_all_by_farmer(
        self,
        farmer_id,
    ):

        return self.farms


class MockCropRepository:

    def __init__(self, crop=None):

        self.crop = crop

    def get_active_by_farm(
        self,
        farm_id,
    ):

        return self.crop


class MockActivityRepository:

    def __init__(self, activities=None):

        self.activities = activities or []

    def get_today_activities(
        self,
        crop_id,
        activity_date,
    ):

        return self.activities


class MockWeatherService:

    def __init__(self, weather=None):

        self.weather = weather or create_weather()

        self.calls = []

    async def get_current_weather(
        self,
        *,
        latitude,
        longitude,
        location=None,
    ):

        self.calls.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "location": location,
            }
        )

        return self.weather


class MockAdvisorPlanner:

    def __init__(self, advice=None):

        self.advice = advice or create_advice()

        self.context = None
        self.calls = 0

    async def generate_daily_advice(
        self,
        *,
        context,
    ):

        self.calls += 1
        self.context = context

        return self.advice


# ============================================================
# SUCCESS
# ============================================================


@pytest.mark.asyncio
async def test_get_today_advice_success():

    farmer = create_farmer()
    farm = create_farm()
    crop = create_crop()

    farm_repository = MockFarmRepository(
        farms=[farm],
    )

    crop_repository = MockCropRepository(
        crop=crop,
    )

    activity_repository = MockActivityRepository(
        activities=[
            create_activity(
                "Irrigate field",
            ),
            create_activity(
                "Inspect crop",
            ),
        ],
    )

    service = AdvisorService(
        farm_repository=farm_repository,
        crop_repository=crop_repository,
        activity_repository=activity_repository,
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    result = await service.get_today_advice(
        current_farmer=farmer,
    )

    assert isinstance(
        result,
        DailyAdvisorResponse,
    )

    assert result.summary == (
        "Conditions are suitable for normal "
        "farm activities today."
    )

    assert result.priority == AdvicePriority.LOW

    assert planner.calls == 1


# ============================================================
# NO FARM
# ============================================================


@pytest.mark.asyncio
async def test_get_today_advice_fails_when_farmer_has_no_farms():

    farmer = create_farmer()

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[],
        ),
        crop_repository=MockCropRepository(),
        activity_repository=MockActivityRepository(),
    )

    with pytest.raises(
        ValidationError,
        match="Farmer has no farms.",
    ):

        await service.get_today_advice(
            current_farmer=farmer,
        )


# ============================================================
# PRIMARY FARM
# ============================================================


@pytest.mark.asyncio
async def test_primary_farm_is_selected():

    farmer = create_farmer()

    first_farm = create_farm(
        is_primary=False,
    )

    primary_farm = create_farm(
        is_primary=True,
    )

    crop = create_crop()

    crop_repository = MockCropRepository(
        crop=crop,
    )

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[
                first_farm,
                primary_farm,
            ],
        ),
        crop_repository=crop_repository,
        activity_repository=MockActivityRepository(),
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    await service.get_today_advice(
        current_farmer=farmer,
    )

    assert weather_service.calls[0]["latitude"] == (
        primary_farm.latitude
    )

    assert weather_service.calls[0]["longitude"] == (
        primary_farm.longitude
    )


# ============================================================
# FALLBACK FARM
# ============================================================


@pytest.mark.asyncio
async def test_first_farm_is_used_when_no_primary_farm():

    farmer = create_farmer()

    first_farm = create_farm(
        is_primary=False,
        latitude=12.111,
        longitude=78.222,
    )

    second_farm = create_farm(
        is_primary=False,
        latitude=13.333,
        longitude=79.444,
    )

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[
                first_farm,
                second_farm,
            ],
        ),
        crop_repository=MockCropRepository(
            crop=create_crop(),
        ),
        activity_repository=MockActivityRepository(),
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    await service.get_today_advice(
        current_farmer=farmer,
    )

    assert weather_service.calls[0]["latitude"] == 12.111
    assert weather_service.calls[0]["longitude"] == 78.222


# ============================================================
# MISSING LATITUDE
# ============================================================


@pytest.mark.asyncio
async def test_missing_latitude_fails():

    farmer = create_farmer()

    farm = create_farm(
        latitude=None,
    )

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[farm],
        ),
        crop_repository=MockCropRepository(
            crop=create_crop(),
        ),
        activity_repository=MockActivityRepository(),
    )

    with pytest.raises(
        ValidationError,
        match="Farm location is required",
    ):

        await service.get_today_advice(
            current_farmer=farmer,
        )


# ============================================================
# MISSING LONGITUDE
# ============================================================


@pytest.mark.asyncio
async def test_missing_longitude_fails():

    farmer = create_farmer()

    farm = create_farm(
        longitude=None,
    )

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[farm],
        ),
        crop_repository=MockCropRepository(
            crop=create_crop(),
        ),
        activity_repository=MockActivityRepository(),
    )

    with pytest.raises(
        ValidationError,
        match="Farm location is required",
    ):

        await service.get_today_advice(
            current_farmer=farmer,
        )


# ============================================================
# NO ACTIVE CROP
# ============================================================


@pytest.mark.asyncio
async def test_no_active_crop_fails():

    farmer = create_farmer()

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[create_farm()],
        ),
        crop_repository=MockCropRepository(
            crop=None,
        ),
        activity_repository=MockActivityRepository(),
    )

    with pytest.raises(
        ValidationError,
        match="No active crop season found.",
    ):

        await service.get_today_advice(
            current_farmer=farmer,
        )


# ============================================================
# CROP AGE
# ============================================================


@pytest.mark.asyncio
async def test_crop_age_is_calculated_correctly():

    farmer = create_farmer()

    crop = create_crop(
        sowing_date=(
            date.today()
            - timedelta(days=60)
        ),
    )

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[create_farm()],
        ),
        crop_repository=MockCropRepository(
            crop=crop,
        ),
        activity_repository=MockActivityRepository(),
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    await service.get_today_advice(
        current_farmer=farmer,
    )

    assert planner.context.crop_age_days == 60


# ============================================================
# FUTURE SOWING DATE
# ============================================================


@pytest.mark.asyncio
async def test_future_sowing_date_returns_zero_crop_age():

    farmer = create_farmer()

    crop = create_crop(
        sowing_date=(
            date.today()
            + timedelta(days=10)
        ),
    )

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[create_farm()],
        ),
        crop_repository=MockCropRepository(
            crop=crop,
        ),
        activity_repository=MockActivityRepository(),
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    await service.get_today_advice(
        current_farmer=farmer,
    )

    assert planner.context.crop_age_days == 0


# ============================================================
# LOCATION
# ============================================================


@pytest.mark.asyncio
async def test_location_is_built_correctly():

    farmer = create_farmer()

    farm = create_farm()

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[farm],
        ),
        crop_repository=MockCropRepository(
            crop=create_crop(),
        ),
        activity_repository=MockActivityRepository(),
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    await service.get_today_advice(
        current_farmer=farmer,
    )

    assert planner.context.location == (
        "Kavali, Nellore"
    )


# ============================================================
# LOCATION WITH MISSING VILLAGE
# ============================================================


@pytest.mark.asyncio
async def test_location_handles_missing_village():

    farmer = create_farmer()

    farm = create_farm()
    farm.village = None

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[farm],
        ),
        crop_repository=MockCropRepository(
            crop=create_crop(),
        ),
        activity_repository=MockActivityRepository(),
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    await service.get_today_advice(
        current_farmer=farmer,
    )

    assert planner.context.location == "Nellore"


# ============================================================
# WEATHER
# ============================================================


@pytest.mark.asyncio
async def test_weather_is_added_to_context():

    farmer = create_farmer()

    weather = create_weather()

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[create_farm()],
        ),
        crop_repository=MockCropRepository(
            crop=create_crop(),
        ),
        activity_repository=MockActivityRepository(),
    )

    weather_service = MockWeatherService(
        weather=weather,
    )

    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    await service.get_today_advice(
        current_farmer=farmer,
    )

    context = planner.context

    assert context.weather == "Clear Sky"
    assert context.temperature == 32.5
    assert context.humidity == 70
    assert context.rain_probability == 20


# ============================================================
# ACTIVITIES
# ============================================================


@pytest.mark.asyncio
async def test_today_activities_are_added_to_context():

    farmer = create_farmer()

    activities = [
        create_activity(
            "Irrigate field",
        ),
        create_activity(
            "Inspect crop",
        ),
        create_activity(
            "Apply fertilizer",
        ),
    ]

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[create_farm()],
        ),
        crop_repository=MockCropRepository(
            crop=create_crop(),
        ),
        activity_repository=MockActivityRepository(
            activities=activities,
        ),
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    await service.get_today_advice(
        current_farmer=farmer,
    )

    assert planner.context.today_activities == [
        "Irrigate field",
        "Inspect crop",
        "Apply fertilizer",
    ]


# ============================================================
# NO ACTIVITIES
# ============================================================


@pytest.mark.asyncio
async def test_no_activities_returns_empty_list():

    farmer = create_farmer()

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[create_farm()],
        ),
        crop_repository=MockCropRepository(
            crop=create_crop(),
        ),
        activity_repository=MockActivityRepository(
            activities=[],
        ),
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    await service.get_today_advice(
        current_farmer=farmer,
    )

    assert planner.context.today_activities == []


# ============================================================
# COMPLETE CONTEXT
# ============================================================


@pytest.mark.asyncio
async def test_complete_ai_context():

    farmer = create_farmer()

    farm = create_farm()

    crop = create_crop(
        sowing_date=(
            date.today()
            - timedelta(days=45)
        ),
    )

    activities = [
        create_activity(
            "Irrigate field",
        ),
    ]

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[farm],
        ),
        crop_repository=MockCropRepository(
            crop=crop,
        ),
        activity_repository=MockActivityRepository(
            activities=activities,
        ),
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    await service.get_today_advice(
        current_farmer=farmer,
    )

    context = planner.context

    assert isinstance(
        context,
        AIContext,
    )

    assert context.crop_name == "Rice"
    assert context.crop_variety == "BPT 5204"
    assert context.crop_age_days == 45
    assert context.soil_type == "Clay Loam"
    assert context.location == "Kavali, Nellore"
    assert context.weather == "Clear Sky"
    assert context.temperature == 32.5
    assert context.humidity == 70
    assert context.rain_probability == 20
    assert context.today_activities == [
        "Irrigate field",
    ]


# ============================================================
# WEATHER CALL
# ============================================================


@pytest.mark.asyncio
async def test_weather_service_receives_correct_location():

    farmer = create_farmer()

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[create_farm()],
        ),
        crop_repository=MockCropRepository(
            crop=create_crop(),
        ),
        activity_repository=MockActivityRepository(),
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    await service.get_today_advice(
        current_farmer=farmer,
    )

    assert len(weather_service.calls) == 1

    assert weather_service.calls[0] == {
        "latitude": 14.4426,
        "longitude": 79.9865,
        "location": "Kavali, Nellore",
    }


# ============================================================
# PLANNER CALL
# ============================================================


@pytest.mark.asyncio
async def test_planner_is_called_once():

    farmer = create_farmer()

    service = AdvisorService(
        farm_repository=MockFarmRepository(
            farms=[create_farm()],
        ),
        crop_repository=MockCropRepository(
            crop=create_crop(),
        ),
        activity_repository=MockActivityRepository(),
    )

    weather_service = MockWeatherService()
    planner = MockAdvisorPlanner()

    service.weather_service = weather_service
    service.planner = planner

    result = await service.get_today_advice(
        current_farmer=farmer,
    )

    assert planner.calls == 1
    assert result == create_advice()