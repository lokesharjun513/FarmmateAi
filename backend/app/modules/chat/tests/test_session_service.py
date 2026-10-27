from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.modules.chat.models import (
    AskFMSessionStatus,
)
from app.modules.chat.session_service import (
    SESSION_TIMEOUT_MINUTES,
    SessionService,
)


class MockRepository:

    def __init__(self):

        self.created = None
        self.updated = None
        self.active_session = None

    def get_active_session(self, farmer_id):

        return self.active_session

    def create(self, session):

        self.created = session

        return session

    def update(self, session):

        self.updated = session

        return session


def create_farmer():

    return SimpleNamespace(
        id=uuid4(),
    )


def test_create_new_session():

    repository = MockRepository()

    service = SessionService(
        repository=repository,
    )

    farmer = create_farmer()

    session = service.get_or_create_session(
        farmer,
    )

    assert session is repository.created

    assert session.farmer_id == farmer.id

    assert (
        session.status
        == AskFMSessionStatus.ACTIVE
    )

    assert session.started_at is not None

    assert session.last_activity_at is not None

    assert session.expires_at is not None


def test_new_session_timeout():

    repository = MockRepository()

    service = SessionService(
        repository=repository,
    )

    farmer = create_farmer()

    session = service.get_or_create_session(
        farmer,
    )

    difference = (
        session.expires_at
        - session.last_activity_at
    )

    assert (
        difference.total_seconds()
        == SESSION_TIMEOUT_MINUTES * 60
    )


def test_existing_active_session_is_refreshed():

    repository = MockRepository()

    existing = SimpleNamespace(
        id=uuid4(),
        farmer_id=uuid4(),
        status=AskFMSessionStatus.ACTIVE,
        started_at=datetime.now(timezone.utc),
        last_activity_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
    )

    repository.active_session = existing

    service = SessionService(
        repository=repository,
    )

    farmer = SimpleNamespace(
        id=existing.farmer_id,
    )

    result = service.get_or_create_session(
        farmer,
    )

    assert result is existing

    assert repository.updated is existing

    assert (
        result.status
        == AskFMSessionStatus.ACTIVE
    )


def test_expire_session():

    repository = MockRepository()

    service = SessionService(
        repository=repository,
    )

    session = SimpleNamespace(
        status=AskFMSessionStatus.ACTIVE,
    )

    result = service.expire_session(
        session,
    )

    assert (
        result.status
        == AskFMSessionStatus.EXPIRED
    )

    assert repository.updated is session