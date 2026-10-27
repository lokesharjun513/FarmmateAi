from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.scheduler import jobs


# ============================================================
# RUN SCHEDULER JOB - SUCCESS
# ============================================================


@pytest.mark.asyncio
async def test_run_scheduler_job_success(monkeypatch):

    db = MagicMock()

    monkeypatch.setattr(
        jobs,
        "SessionLocal",
        MagicMock(return_value=db),
    )

    result = SimpleNamespace(
        model_dump=lambda: {
            "processed_farms": 2,
            "processed_crop_seasons": 2,
            "weather_updated": 2,
            "advisor_generated": 2,
            "notifications_created": 2,
            "expired_sessions": 1,
            "completed": True,
        },
    )

    service = MagicMock()

    service.run = AsyncMock(
        return_value=result,
    )

    monkeypatch.setattr(
        jobs,
        "SchedulerService",
        MagicMock(return_value=service),
    )

    await jobs.run_scheduler_job()

    service.run.assert_awaited_once()

    db.close.assert_called_once()


# ============================================================
# RUN SCHEDULER JOB - FAILURE
# ============================================================


@pytest.mark.asyncio
async def test_run_scheduler_job_handles_failure(monkeypatch):

    db = MagicMock()

    monkeypatch.setattr(
        jobs,
        "SessionLocal",
        MagicMock(return_value=db),
    )

    service = MagicMock()

    service.run = AsyncMock(
        side_effect=Exception(
            "Scheduler failure",
        ),
    )

    monkeypatch.setattr(
        jobs,
        "SchedulerService",
        MagicMock(return_value=service),
    )

    # The function catches exceptions internally.
    await jobs.run_scheduler_job()

    service.run.assert_awaited_once()

    # Database must always close.
    db.close.assert_called_once()


# ============================================================
# START SCHEDULER
# ============================================================


def test_start_scheduler(monkeypatch):

    scheduler = MagicMock()

    scheduler.running = False

    monkeypatch.setattr(
        jobs,
        "scheduler",
        scheduler,
    )

    jobs.start_scheduler()

    scheduler.add_job.assert_called_once()

    scheduler.start.assert_called_once()


# ============================================================
# START SCHEDULER - ALREADY RUNNING
# ============================================================


def test_start_scheduler_does_not_start_duplicate(monkeypatch):

    scheduler = MagicMock()

    scheduler.running = True

    monkeypatch.setattr(
        jobs,
        "scheduler",
        scheduler,
    )

    jobs.start_scheduler()

    scheduler.add_job.assert_not_called()

    scheduler.start.assert_not_called()