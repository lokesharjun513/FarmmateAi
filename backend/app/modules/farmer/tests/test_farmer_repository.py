from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.farmer.models import Farmer
from app.modules.farmer.repository import FarmerRepository


# ============================================================
# HELPER
# ============================================================


def create_farmer(
    db,
    *,
    user_id=None,
    preferred_language="English",
    experience_years=None,
):

    farmer = Farmer(
        user_id=user_id or uuid4(),
        preferred_language=preferred_language,
        experience_years=experience_years,
        profile_completion=0,
        onboarding_completed=False,
    )

    db.add(farmer)
    db.commit()
    db.refresh(farmer)

    return farmer


# ============================================================
# GET BY USER ID
# ============================================================


def test_get_by_user_id(db):

    user_id = uuid4()

    farmer = create_farmer(
        db,
        user_id=user_id,
    )

    repository = FarmerRepository(db)

    result = repository.get_by_user_id(
        user_id,
    )

    assert result is not None
    assert result.id == farmer.id
    assert result.user_id == user_id


# ============================================================
# GET BY USER ID - NOT FOUND
# ============================================================


def test_get_by_user_id_not_found(db):

    repository = FarmerRepository(db)

    result = repository.get_by_user_id(
        uuid4(),
    )

    assert result is None


# ============================================================
# GET BY FARMER ID
# ============================================================


def test_get_by_id(db):

    farmer = create_farmer(db)

    repository = FarmerRepository(db)

    result = repository.get_by_id(
        farmer.id,
    )

    assert result is not None
    assert result.id == farmer.id


# ============================================================
# GET BY FARMER ID - NOT FOUND
# ============================================================


def test_get_by_id_not_found(db):

    repository = FarmerRepository(db)

    result = repository.get_by_id(
        uuid4(),
    )

    assert result is None


# ============================================================
# CREATE
# ============================================================


def test_create_farmer(db):

    user_id = uuid4()

    farmer = Farmer(
        user_id=user_id,
        preferred_language="Telugu",
        experience_years=5,
        profile_completion=0,
        onboarding_completed=False,
    )

    repository = FarmerRepository(db)

    result = repository.create(
        farmer,
    )

    assert result.id is not None
    assert result.user_id == user_id
    assert result.preferred_language == "Telugu"
    assert result.experience_years == 5


# ============================================================
# CREATE DEFAULT VALUES
# ============================================================


def test_create_farmer_defaults(db):

    farmer = Farmer(
        user_id=uuid4(),
    )

    repository = FarmerRepository(db)

    result = repository.create(
        farmer,
    )

    assert result.preferred_language == "English"
    assert result.profile_completion == 0
    assert result.onboarding_completed is False


# ============================================================
# DUPLICATE USER ID
# ============================================================


def test_duplicate_user_id_fails(db):

    user_id = uuid4()

    create_farmer(
        db,
        user_id=user_id,
    )

    duplicate = Farmer(
        user_id=user_id,
        preferred_language="Telugu",
    )

    repository = FarmerRepository(db)

    with pytest.raises(
        IntegrityError,
    ):

        repository.create(
            duplicate,
        )


# ============================================================
# UPDATE
# ============================================================


def test_update_farmer(db):

    farmer = create_farmer(
        db,
        preferred_language="English",
        experience_years=2,
    )

    farmer.preferred_language = "Telugu"
    farmer.experience_years = 10

    repository = FarmerRepository(db)

    result = repository.update(
        farmer,
    )

    assert result.preferred_language == "Telugu"
    assert result.experience_years == 10


# ============================================================
# UPDATE PERSISTS
# ============================================================


def test_update_farmer_persists(db):

    farmer = create_farmer(
        db,
        preferred_language="English",
    )

    farmer.preferred_language = "Hindi"

    repository = FarmerRepository(db)

    repository.update(
        farmer,
    )

    result = repository.get_by_id(
        farmer.id,
    )

    assert result is not None
    assert result.preferred_language == "Hindi"


# ============================================================
# UPDATE EXPERIENCE
# ============================================================


def test_update_experience(db):

    farmer = create_farmer(
        db,
        experience_years=5,
    )

    farmer.experience_years = 15

    repository = FarmerRepository(db)

    result = repository.update(
        farmer,
    )

    assert result.experience_years == 15


# ============================================================
# CLEAR EXPERIENCE
# ============================================================


def test_update_can_clear_experience(db):

    farmer = create_farmer(
        db,
        experience_years=10,
    )

    farmer.experience_years = None

    repository = FarmerRepository(db)

    result = repository.update(
        farmer,
    )

    assert result.experience_years is None