from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.modules.ai_engine.context_builder import AIContextBuilder

# ============================================================
# MOCKS
# ============================================================


class FakeFarmRepository:

    def __init__(self, farms):

        self.farms = farms

    def get_all_by_farmer(self, farmer_id):

        return self.farms


class FakeCropRepository:

    def __init__(self, crop):

        self.crop = crop

    def get_active_by_farm(self, farm_id):

        return self.crop


class FakeActivityRepository:

    def __init__(self, activities):

        self.activities = activities

    def get_today_activities(
        self,
        crop_id,
        activity_date,
    ):

        return self.activities


class FakeWeatherService:

    def __init__(
        self,
        *,
        weather=None,
        error=None,
    ):
        self.weather = weather
        self.error = error
        self.called = False

    async def get_current_weather(
        self,
        *,
        latitude,
        longitude,
        location,
    ):

        self.called = True

        if self.error is not None:

            raise self.error

        return self.weather


def create_farm(**overrides):

    values = {
        "id": uuid4(),
        "is_primary": True,
        "latitude": 14.4426,
        "longitude": 79.9865,
        "village": "Nellore",
        "mandal": None,
        "district": "Nellore",
        "state": "Andhra Pradesh",
        "soil_type": "Clay",
    }

    values.update(overrides)

    return SimpleNamespace(**values)


def create_crop():

    return SimpleNamespace(
        id=uuid4(),
        crop_name="Rice",
        crop_variety="BPT 5204",
        sowing_date=(
            datetime.now(UTC).date()
            - timedelta(days=45)
        ),
    )


def create_weather():

    return SimpleNamespace(
        weather_condition="Clear Sky",
        temperature=32.5,
        humidity=70,
        rain_probability=20,
    )


def create_builder(
    *,
    farms,
    crop=None,
    activities=None,
    weather_service=None,
):

    return AIContextBuilder(
        farm_repository=FakeFarmRepository(farms),
        crop_repository=FakeCropRepository(crop),
        activity_repository=FakeActivityRepository(
            activities or [],
        ),
        weather_service=(
            weather_service or FakeWeatherService(
                weather=create_weather(),
            )
        ),
    )


# ============================================================
# CONTEXT
# ============================================================


@pytest.mark.asyncio
async def test_build_returns_complete_context():

    weather_service = FakeWeatherService(
        weather=create_weather(),
    )

    builder = create_builder(
        farms=[create_farm()],
        crop=create_crop(),
        activities=[
            SimpleNamespace(title="Irrigate field"),
        ],
        weather_service=weather_service,
    )

    result = await builder.build(
        SimpleNamespace(id=uuid4()),
    )

    assert result.crop_name == "Rice"
    assert result.crop_variety == "BPT 5204"
    assert result.crop_age_days == 45
    assert result.soil_type == "Clay"
    assert result.location == (
        "Nellore, Nellore, Andhra Pradesh"
    )
    assert result.weather == "Clear Sky"
    assert result.temperature == 32.5
    assert result.humidity == 70
    assert result.rain_probability == 20
    assert result.today_activities == [
        "Irrigate field",
    ]
    assert weather_service.called is True


@pytest.mark.asyncio
async def test_build_allows_farmer_without_farms():

    weather_service = FakeWeatherService(
        weather=create_weather(),
    )

    builder = create_builder(
        farms=[],
        weather_service=weather_service,
    )

    result = await builder.build(
        SimpleNamespace(id=uuid4()),
    )

    assert result.crop_name == "Unknown"
    assert result.location == "Unknown"
    assert result.weather == "Unknown"
    assert result.today_activities == []
    assert weather_service.called is False


@pytest.mark.asyncio
async def test_build_allows_farm_without_active_crop():

    builder = create_builder(
        farms=[create_farm()],
        crop=None,
    )

    result = await builder.build(
        SimpleNamespace(id=uuid4()),
    )

    assert result.crop_name == "Unknown"
    assert result.crop_variety is None
    assert result.crop_age_days == 0
    assert result.location == (
        "Nellore, Nellore, Andhra Pradesh"
    )
    assert result.weather == "Clear Sky"
    assert result.today_activities == []


@pytest.mark.asyncio
async def test_build_continues_when_weather_fails():

    builder = create_builder(
        farms=[create_farm()],
        crop=create_crop(),
        weather_service=FakeWeatherService(
            error=RuntimeError("Weather unavailable."),
        ),
    )

    result = await builder.build(
        SimpleNamespace(id=uuid4()),
    )

    assert result.crop_name == "Rice"
    assert result.weather == "Unknown"
    assert result.temperature == 0.0
    assert result.humidity == 0
    assert result.rain_probability == 0


@pytest.mark.asyncio
async def test_build_skips_weather_without_coordinates():

    weather_service = FakeWeatherService(
        weather=create_weather(),
    )

    builder = create_builder(
        farms=[
            create_farm(
                latitude=None,
                longitude=None,
            )
        ],
        crop=create_crop(),
        weather_service=weather_service,
    )

    result = await builder.build(
        SimpleNamespace(id=uuid4()),
    )

    assert result.weather == "Unknown"
    assert result.location == (
        "Nellore, Nellore, Andhra Pradesh"
    )
    assert weather_service.called is False
