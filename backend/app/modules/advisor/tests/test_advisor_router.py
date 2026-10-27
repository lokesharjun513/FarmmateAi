from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.dependencies import get_current_farmer
from app.database.session import get_db

from app.modules.advisor.router import router
from app.modules.advisor.schemas import (
    AdvicePriority,
    DailyAdvisorResponse,
)


# ============================================================
# TEST APP
# ============================================================


app = FastAPI()

app.include_router(router)


# ============================================================
# TEST DATA
# ============================================================


FARMER_ID = uuid4()


def create_farmer():

    return SimpleNamespace(
        id=FARMER_ID,
    )


def create_advice():

    return DailyAdvisorResponse(
        summary=(
            "Weather conditions are suitable "
            "for normal farm activities."
        ),
        warnings=[
            "Monitor soil moisture.",
        ],
        recommendations=[
            "Check field moisture.",
            "Inspect the crop.",
            "Complete necessary farm activities.",
        ],
        priority=AdvicePriority.LOW,
    )


# ============================================================
# DATABASE
# ============================================================


@pytest.fixture
def db():

    return SimpleNamespace()


# ============================================================
# CURRENT FARMER
# ============================================================


@pytest.fixture
def mock_farmer():

    return create_farmer()


# ============================================================
# CLIENT
# ============================================================


@pytest.fixture
def client(mock_farmer, db):

    def override_current_farmer():

        return mock_farmer

    def override_db():

        yield db

    app.dependency_overrides[
        get_current_farmer
    ] = override_current_farmer

    app.dependency_overrides[
        get_db
    ] = override_db

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


# ============================================================
# SUCCESS
# ============================================================


def test_get_today_advice_success(
    client,
    monkeypatch,
):

    advice = create_advice()

    class MockAdvisorService:

        def __init__(
            self,
            *,
            farm_repository,
            crop_repository,
            activity_repository,
        ):

            pass

        async def get_today_advice(
            self,
            *,
            current_farmer,
        ):

            return advice

    monkeypatch.setattr(
        "app.modules.advisor.router.AdvisorService",
        MockAdvisorService,
    )

    response = client.get(
        "/advisor/today",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert data["message"] == (
        "Daily advisor generated successfully."
    )

    assert data["data"]["summary"] == (
        "Weather conditions are suitable "
        "for normal farm activities."
    )

    assert data["data"]["priority"] == "LOW"

    assert data["data"]["warnings"] == [
        "Monitor soil moisture.",
    ]

    assert data["data"]["recommendations"] == [
        "Check field moisture.",
        "Inspect the crop.",
        "Complete necessary farm activities.",
    ]


# ============================================================
# HIGH PRIORITY RESPONSE
# ============================================================


def test_get_today_advice_high_priority(
    client,
    monkeypatch,
):

    advice = DailyAdvisorResponse(
        summary="Heavy rain is expected today.",
        warnings=[
            "Avoid pesticide spraying.",
            "Delay fertilizer application.",
        ],
        recommendations=[
            "Protect the crop from heavy rain.",
            "Check field drainage.",
            "Avoid unnecessary field work.",
        ],
        priority=AdvicePriority.HIGH,
    )

    class MockAdvisorService:

        def __init__(
            self,
            *,
            farm_repository,
            crop_repository,
            activity_repository,
        ):

            pass

        async def get_today_advice(
            self,
            *,
            current_farmer,
        ):

            return advice

    monkeypatch.setattr(
        "app.modules.advisor.router.AdvisorService",
        MockAdvisorService,
    )

    response = client.get(
        "/advisor/today",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["data"]["priority"] == "HIGH"


# ============================================================
# MEDIUM PRIORITY RESPONSE
# ============================================================


def test_get_today_advice_medium_priority(
    client,
    monkeypatch,
):

    advice = DailyAdvisorResponse(
        summary="Moderate weather risk requires attention.",
        warnings=[
            "Monitor soil moisture.",
        ],
        recommendations=[
            "Inspect the crop.",
            "Monitor weather conditions.",
            "Adjust irrigation if necessary.",
        ],
        priority=AdvicePriority.MEDIUM,
    )

    class MockAdvisorService:

        def __init__(
            self,
            *,
            farm_repository,
            crop_repository,
            activity_repository,
        ):

            pass

        async def get_today_advice(
            self,
            *,
            current_farmer,
        ):

            return advice

    monkeypatch.setattr(
        "app.modules.advisor.router.AdvisorService",
        MockAdvisorService,
    )

    response = client.get(
        "/advisor/today",
    )

    assert response.status_code == 200

    assert response.json()["data"]["priority"] == "MEDIUM"


# ============================================================
# SERVICE ERROR
# ============================================================


def test_get_today_advice_service_error(
    client,
    monkeypatch,
):

    class MockAdvisorService:

        def __init__(
            self,
            *,
            farm_repository,
            crop_repository,
            activity_repository,
        ):

            pass

        async def get_today_advice(
            self,
            *,
            current_farmer,
        ):

            raise ValueError(
                "Advisor service failed.",
            )

    monkeypatch.setattr(
        "app.modules.advisor.router.AdvisorService",
        MockAdvisorService,
    )

    with pytest.raises(
        ValueError,
        match="Advisor service failed.",
    ):

        client.get(
            "/advisor/today",
        )


# ============================================================
# METHOD NOT ALLOWED
# ============================================================


def test_advisor_today_post_not_allowed(
    client,
    monkeypatch,
):

    class MockAdvisorService:

        def __init__(
            self,
            *,
            farm_repository,
            crop_repository,
            activity_repository,
        ):

            pass

    monkeypatch.setattr(
        "app.modules.advisor.router.AdvisorService",
        MockAdvisorService,
    )

    response = client.post(
        "/advisor/today",
    )

    assert response.status_code == 405