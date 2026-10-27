from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.onboarding.router import router


# ============================================================
# APP
# ============================================================


app = FastAPI()

app.include_router(router)


# ============================================================
# HELPERS
# ============================================================


def make_user():

    return SimpleNamespace(
        id=uuid4(),
    )


def make_farmer(
    profile_completion: int,
):

    return SimpleNamespace(
        profile_completion=profile_completion,
    )


class FakeFarmerRepository:

    farmer = None

    def __init__(self, db):

        self.db = db

    def get_by_user_id(
        self,
        user_id,
    ):

        return self.farmer


# ============================================================
# OVERRIDE AUTH
# ============================================================


def fake_current_user():

    return make_user()


def fake_db():

    return object()


# ============================================================
# APPLY OVERRIDES
# ============================================================


from app.core.auth import get_current_user
from app.database.session import get_db


app.dependency_overrides[
    get_current_user
] = fake_current_user

app.dependency_overrides[
    get_db
] = fake_db


client = TestClient(app)


# ============================================================
# NO FARMER
# ============================================================


def test_next_step_without_farmer(
    monkeypatch,
):

    FakeFarmerRepository.farmer = None

    monkeypatch.setattr(
        "app.modules.onboarding.router.FarmerRepository",
        FakeFarmerRepository,
    )

    response = client.get(
        "/onboarding/next",
    )

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "step": "language",
        "title": "Welcome to FarmMate AI",
        "message": "Which language do you prefer?",
        "progress": 0,
        "completed": False,
    }


# ============================================================
# PROFILE < 20
# ============================================================


def test_next_step_profile_incomplete(
    monkeypatch,
):

    FakeFarmerRepository.farmer = (
        make_farmer(10)
    )

    monkeypatch.setattr(
        "app.modules.onboarding.router.FarmerRepository",
        FakeFarmerRepository,
    )

    response = client.get(
        "/onboarding/next",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["step"] == "language"
    assert data["progress"] == 10
    assert data["completed"] is False


# ============================================================
# FARM STEP
# ============================================================


def test_next_step_farm(
    monkeypatch,
):

    FakeFarmerRepository.farmer = (
        make_farmer(50)
    )

    monkeypatch.setattr(
        "app.modules.onboarding.router.FarmerRepository",
        FakeFarmerRepository,
    )

    response = client.get(
        "/onboarding/next",
    )

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "step": "farm",
        "title": "Let's add your first farm",
        "message": "Tell me about your farm.",
        "progress": 50,
        "completed": False,
    }


# ============================================================
# COMPLETED
# ============================================================


def test_next_step_completed(
    monkeypatch,
):

    FakeFarmerRepository.farmer = (
        make_farmer(100)
    )

    monkeypatch.setattr(
        "app.modules.onboarding.router.FarmerRepository",
        FakeFarmerRepository,
    )

    response = client.get(
        "/onboarding/next",
    )

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "step": "completed",
        "title": "You're all set!",
        "message": "Let's start farming.",
        "progress": 100,
        "completed": True,
    }


# ============================================================
# RESPONSE STRUCTURE
# ============================================================


def test_next_step_response_contains_expected_fields(
    monkeypatch,
):

    FakeFarmerRepository.farmer = (
        make_farmer(50)
    )

    monkeypatch.setattr(
        "app.modules.onboarding.router.FarmerRepository",
        FakeFarmerRepository,
    )

    response = client.get(
        "/onboarding/next",
    )

    assert response.status_code == 200

    data = response.json()

    assert set(data.keys()) == {
        "step",
        "title",
        "message",
        "progress",
        "completed",
    }


# ============================================================
# AUTHENTICATION
# ============================================================


def test_next_step_requires_authentication():

    protected_app = FastAPI()

    protected_app.include_router(
        router,
    )

    protected_client = TestClient(
        protected_app,
    )

    response = protected_client.get(
        "/onboarding/next",
    )

    assert response.status_code in {
        401,
        403,
    }