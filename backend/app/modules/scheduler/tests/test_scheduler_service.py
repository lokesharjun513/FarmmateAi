from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.notifications.models import (
    NotificationPriority,
    NotificationType,
)
from app.modules.scheduler.service import SchedulerService


# ============================================================
# HELPERS
# ============================================================


def create_service():

    farm_repository = MagicMock()
    farmer_repository = MagicMock()
    crop_repository = MagicMock()
    activity_repository = MagicMock()
    notification_repository = MagicMock()
    session_repository = MagicMock()

    service = SchedulerService(
        farm_repository=farm_repository,
        farmer_repository=farmer_repository,
        crop_repository=crop_repository,
        activity_repository=activity_repository,
        notification_repository=notification_repository,
        session_repository=session_repository,
    )

    return (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    )


def create_farm(
    *,
    farmer_id=None,
    latitude=14.4426,
    longitude=79.9865,
):

    return SimpleNamespace(
        id=uuid4(),
        farmer_id=farmer_id or uuid4(),
        latitude=latitude,
        longitude=longitude,
        village="Test Village",
        district="Nellore",
    )


def create_farmer():

    return SimpleNamespace(
        id=uuid4(),
    )


def create_crop():

    return SimpleNamespace(
        id=uuid4(),
    )


def create_advice():

    return SimpleNamespace(
        summary="Apply irrigation today.",
    )


# ============================================================
# NO FARMS
# ============================================================


@pytest.mark.asyncio
async def test_scheduler_with_no_farms():

    (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    ) = create_service()

    farm_repository.get_all.return_value = []

    session_repository.delete_expired_sessions.return_value = 3

    result = await service.run()

    assert result.processed_farms == 0
    assert result.processed_crop_seasons == 0
    assert result.weather_updated == 0
    assert result.advisor_generated == 0
    assert result.notifications_created == 0
    assert result.expired_sessions == 3
    assert result.completed is True

    crop_repository.get_active_by_farm.assert_not_called()
    farmer_repository.get_by_id.assert_not_called()
    notification_repository.create.assert_not_called()


# ============================================================
# FARM WITHOUT ACTIVE CROP
# ============================================================


@pytest.mark.asyncio
async def test_scheduler_skips_farm_without_active_crop():

    (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    ) = create_service()

    farmer_id = uuid4()

    farm = create_farm(
        farmer_id=farmer_id,
    )

    farm_repository.get_all.return_value = [farm]

    crop_repository.get_active_by_farm.return_value = None

    session_repository.delete_expired_sessions.return_value = 0

    result = await service.run()

    assert result.processed_farms == 1
    assert result.processed_crop_seasons == 0
    assert result.weather_updated == 0
    assert result.advisor_generated == 0
    assert result.notifications_created == 0
    assert result.expired_sessions == 0
    assert result.completed is True

    crop_repository.get_active_by_farm.assert_called_once_with(
        farm.id,
    )

    farmer_repository.get_by_id.assert_not_called()
    notification_repository.create.assert_not_called()


# ============================================================
# FARM WITH CROP BUT NO LOCATION
# ============================================================


@pytest.mark.asyncio
async def test_scheduler_skips_weather_when_location_missing():

    (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    ) = create_service()

    farmer = create_farmer()

    farm = create_farm(
        farmer_id=farmer.id,
        latitude=None,
        longitude=None,
    )

    crop = create_crop()

    farm_repository.get_all.return_value = [farm]
    crop_repository.get_active_by_farm.return_value = crop
    farmer_repository.get_by_id.return_value = farmer

    service.advisor_service.get_today_advice = AsyncMock(
        return_value=create_advice(),
    )
    service.weather_service.get_current_weather = AsyncMock()
    session_repository.delete_expired_sessions.return_value = 0

    result = await service.run()

    assert result.processed_farms == 1
    assert result.processed_crop_seasons == 1
    assert result.weather_updated == 0
    assert result.advisor_generated == 1
    assert result.notifications_created == 1

    service.weather_service.get_current_weather.assert_not_called()

    notification_repository.create.assert_called_once()


# ============================================================
# WEATHER SUCCESS
# ============================================================


@pytest.mark.asyncio
async def test_scheduler_updates_weather_successfully():

    (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    ) = create_service()

    farmer = create_farmer()
    farm = create_farm(
        farmer_id=farmer.id,
    )
    crop = create_crop()

    farm_repository.get_all.return_value = [farm]
    crop_repository.get_active_by_farm.return_value = crop
    farmer_repository.get_by_id.return_value = farmer

    service.weather_service.get_current_weather = AsyncMock(
        return_value={"temperature": 30},
    )

    service.advisor_service.get_today_advice = AsyncMock(
        return_value=create_advice(),
    )

    session_repository.delete_expired_sessions.return_value = 0

    result = await service.run()

    assert result.weather_updated == 1

    service.weather_service.get_current_weather.assert_awaited_once_with(
        latitude=farm.latitude,
        longitude=farm.longitude,
        location="Test Village, Nellore",
    )


# ============================================================
# WEATHER FAILURE DOES NOT STOP SCHEDULER
# ============================================================


@pytest.mark.asyncio
async def test_scheduler_continues_when_weather_fails():

    (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    ) = create_service()

    farmer = create_farmer()
    farm = create_farm(
        farmer_id=farmer.id,
    )
    crop = create_crop()

    farm_repository.get_all.return_value = [farm]
    crop_repository.get_active_by_farm.return_value = crop
    farmer_repository.get_by_id.return_value = farmer

    service.weather_service.get_current_weather = AsyncMock(
        side_effect=Exception("Weather API failed"),
    )

    service.advisor_service.get_today_advice = AsyncMock(
        return_value=create_advice(),
    )

    session_repository.delete_expired_sessions.return_value = 2

    result = await service.run()

    assert result.processed_farms == 1
    assert result.processed_crop_seasons == 1
    assert result.weather_updated == 0
    assert result.advisor_generated == 1
    assert result.notifications_created == 1
    assert result.expired_sessions == 2
    assert result.completed is True


# ============================================================
# FARMER NOT FOUND
# ============================================================


@pytest.mark.asyncio
async def test_scheduler_skips_when_farmer_not_found():

    (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    ) = create_service()

    farm = create_farm()
    crop = create_crop()

    farm_repository.get_all.return_value = [farm]
    crop_repository.get_active_by_farm.return_value = crop
    farmer_repository.get_by_id.return_value = None

    session_repository.delete_expired_sessions.return_value = 1

    result = await service.run()

    assert result.processed_farms == 1
    assert result.processed_crop_seasons == 1
    assert result.advisor_generated == 0
    assert result.notifications_created == 0
    assert result.expired_sessions == 1

    notification_repository.create.assert_not_called()


# ============================================================
# AI ADVISOR SUCCESS
# ============================================================


@pytest.mark.asyncio
async def test_scheduler_generates_advisor_and_notification():

    (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    ) = create_service()

    farmer = create_farmer()
    farm = create_farm(
        farmer_id=farmer.id,
        latitude=None,
        longitude=None,
    )
    crop = create_crop()
    advice = create_advice()

    farm_repository.get_all.return_value = [farm]
    crop_repository.get_active_by_farm.return_value = crop
    farmer_repository.get_by_id.return_value = farmer

    service.advisor_service.get_today_advice = AsyncMock(
        return_value=advice,
    )

    session_repository.delete_expired_sessions.return_value = 0

    result = await service.run()

    assert result.advisor_generated == 1
    assert result.notifications_created == 1

    notification_repository.create.assert_called_once()

    notification = (
        notification_repository.create.call_args.args[0]
    )

    assert notification.farmer_id == farmer.id
    assert notification.title == "Today's AI Advice"
    assert notification.message == advice.summary
    assert notification.type == NotificationType.AI_ADVISOR
    assert notification.priority == NotificationPriority.MEDIUM
    assert notification.is_read is False


# ============================================================
# AI ADVISOR FAILURE
# ============================================================


@pytest.mark.asyncio
async def test_scheduler_continues_when_advisor_fails():

    (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    ) = create_service()

    farmer = create_farmer()
    farm = create_farm(
        farmer_id=farmer.id,
        latitude=None,
        longitude=None,
    )
    crop = create_crop()

    farm_repository.get_all.return_value = [farm]
    crop_repository.get_active_by_farm.return_value = crop
    farmer_repository.get_by_id.return_value = farmer

    service.advisor_service.get_today_advice = AsyncMock(
        side_effect=Exception("Advisor failed"),
    )

    session_repository.delete_expired_sessions.return_value = 5

    result = await service.run()

    assert result.processed_farms == 1
    assert result.processed_crop_seasons == 1
    assert result.advisor_generated == 0
    assert result.notifications_created == 0
    assert result.expired_sessions == 5
    assert result.completed is True

    notification_repository.create.assert_not_called()


# ============================================================
# MULTIPLE FARMS
# ============================================================


@pytest.mark.asyncio
async def test_scheduler_processes_multiple_farms():

    (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    ) = create_service()

    farmer1 = create_farmer()
    farmer2 = create_farmer()

    farm1 = create_farm(
        farmer_id=farmer1.id,
        latitude=14.0,
        longitude=80.0,
    )

    farm2 = create_farm(
        farmer_id=farmer2.id,
        latitude=15.0,
        longitude=79.0,
    )

    crop1 = create_crop()
    crop2 = create_crop()

    farm_repository.get_all.return_value = [
        farm1,
        farm2,
    ]

    crop_repository.get_active_by_farm.side_effect = [
        crop1,
        crop2,
    ]

    farmer_repository.get_by_id.side_effect = [
        farmer1,
        farmer2,
    ]

    service.weather_service.get_current_weather = AsyncMock(
        return_value={},
    )

    service.advisor_service.get_today_advice = AsyncMock(
        side_effect=[
            create_advice(),
            create_advice(),
        ],
    )

    session_repository.delete_expired_sessions.return_value = 2

    result = await service.run()

    assert result.processed_farms == 2
    assert result.processed_crop_seasons == 2
    assert result.weather_updated == 2
    assert result.advisor_generated == 2
    assert result.notifications_created == 2
    assert result.expired_sessions == 2
    assert result.completed is True

    assert notification_repository.create.call_count == 2


# ============================================================
# EXPIRED SESSION CLEANUP
# ============================================================


@pytest.mark.asyncio
async def test_scheduler_deletes_expired_sessions():

    (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    ) = create_service()

    farm_repository.get_all.return_value = []

    session_repository.delete_expired_sessions.return_value = 7

    result = await service.run()

    assert result.expired_sessions == 7

    session_repository.delete_expired_sessions.assert_called_once()


# ============================================================
# COMPLETED FLAG
# ============================================================


@pytest.mark.asyncio
async def test_scheduler_returns_completed_true():

    (
        service,
        farm_repository,
        farmer_repository,
        crop_repository,
        activity_repository,
        notification_repository,
        session_repository,
    ) = create_service()

    farm_repository.get_all.return_value = []
    session_repository.delete_expired_sessions.return_value = 0

    result = await service.run()

    assert result.completed is True