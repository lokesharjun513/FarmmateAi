from collections.abc import Generator

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.base import Base


# ============================================================
# IMPORT ALL MODELS
# ============================================================

from app.modules.identity.models import User
from app.modules.farmer.models import Farmer
from app.modules.farm.models import Farm
from app.modules.crop_season.models import CropSeason
from app.modules.crop_stage.models import CropStage
from app.modules.activity.models import Activity
from app.modules.notifications.models import Notification
from app.modules.notifications.models_device import DeviceToken
from app.modules.chat.models import AskFMSession


# ============================================================
# TEST DATABASE
# ============================================================

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """
    Create a fresh in-memory SQLite database for each test.

    All models are imported before create_all() so SQLAlchemy
    knows about every table and relationship.
    """

    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    # Create all registered tables.
    Base.metadata.create_all(bind=engine)

    # Create test session.
    with Session(engine) as session:
        yield session

        # Clean up any uncommitted transaction.
        session.rollback()

    # Drop all tables.
    Base.metadata.drop_all(bind=engine)

    # Dispose engine.
    engine.dispose()