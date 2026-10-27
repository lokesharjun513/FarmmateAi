from uuid import uuid4

import pytest

from app.modules.farmer.models import Farmer
from app.modules.farmer.repository import FarmerRepository
from app.modules.farmer.schemas import (
    FarmerCreateRequest,
    FarmerUpdateRequest,
)
from app.modules.farmer.service import (
    create_farmer_profile,
    get_farmer_profile,
    update_farmer_profile,
)
from app.shared.constants import PROFILE_INITIAL
from app.shared.exceptions import (
    FarmerProfileAlreadyExistsError,
    FarmerProfileNotFoundError,
)


# ============================================================
# CREATE
# ============================================================


def test_create_farmer_profile(db):

    repository = FarmerRepository(db)

    user_id = uuid4()

    request = FarmerCreateRequest(
        preferred_language="Telugu",
        experience_years=5,
    )

    result = create_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=request,
    )

    assert result.id is not None
    assert result.user_id == user_id
    assert result.preferred_language == "Telugu"
    assert result.experience_years == 5

    assert result.profile_completion == PROFILE_INITIAL
    assert result.onboarding_completed is False


# ============================================================
# CREATE DEFAULT LANGUAGE
# ============================================================


def test_create_farmer_profile_default_language(db):

    repository = FarmerRepository(db)

    user_id = uuid4()

    request = FarmerCreateRequest()

    result = create_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=request,
    )

    assert result.preferred_language == "English"
    assert result.experience_years is None


# ============================================================
# DUPLICATE PROFILE
# ============================================================


def test_create_duplicate_farmer_profile_fails(db):

    repository = FarmerRepository(db)

    user_id = uuid4()

    first_request = FarmerCreateRequest(
        preferred_language="English",
        experience_years=5,
    )

    create_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=first_request,
    )

    second_request = FarmerCreateRequest(
        preferred_language="Telugu",
        experience_years=10,
    )

    with pytest.raises(
        FarmerProfileAlreadyExistsError,
    ):

        create_farmer_profile(
            repository=repository,
            user_id=user_id,
            request=second_request,
        )


# ============================================================
# GET PROFILE
# ============================================================


def test_get_farmer_profile(db):

    repository = FarmerRepository(db)

    user_id = uuid4()

    request = FarmerCreateRequest(
        preferred_language="Telugu",
        experience_years=7,
    )

    created = create_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=request,
    )

    result = get_farmer_profile(
        repository=repository,
        user_id=user_id,
    )

    assert result.id == created.id
    assert result.user_id == user_id
    assert result.preferred_language == "Telugu"
    assert result.experience_years == 7


# ============================================================
# GET PROFILE NOT FOUND
# ============================================================


def test_get_farmer_profile_not_found(db):

    repository = FarmerRepository(db)

    with pytest.raises(
        FarmerProfileNotFoundError,
    ):

        get_farmer_profile(
            repository=repository,
            user_id=uuid4(),
        )


# ============================================================
# UPDATE LANGUAGE
# ============================================================


def test_update_farmer_language(db):

    repository = FarmerRepository(db)

    user_id = uuid4()

    create_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=FarmerCreateRequest(
            preferred_language="English",
            experience_years=5,
        ),
    )

    request = FarmerUpdateRequest(
        preferred_language="Telugu",
    )

    result = update_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=request,
    )

    assert result.preferred_language == "Telugu"
    assert result.experience_years == 5


# ============================================================
# UPDATE EXPERIENCE
# ============================================================


def test_update_farmer_experience(db):

    repository = FarmerRepository(db)

    user_id = uuid4()

    create_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=FarmerCreateRequest(
            preferred_language="English",
            experience_years=5,
        ),
    )

    request = FarmerUpdateRequest(
        experience_years=12,
    )

    result = update_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=request,
    )

    assert result.preferred_language == "English"
    assert result.experience_years == 12


# ============================================================
# UPDATE BOTH
# ============================================================


def test_update_farmer_both_fields(db):

    repository = FarmerRepository(db)

    user_id = uuid4()

    create_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=FarmerCreateRequest(
            preferred_language="English",
            experience_years=5,
        ),
    )

    request = FarmerUpdateRequest(
        preferred_language="Hindi",
        experience_years=20,
    )

    result = update_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=request,
    )

    assert result.preferred_language == "Hindi"
    assert result.experience_years == 20


# ============================================================
# EMPTY UPDATE
# ============================================================


def test_empty_update_does_nothing(db):

    repository = FarmerRepository(db)

    user_id = uuid4()

    create_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=FarmerCreateRequest(
            preferred_language="English",
            experience_years=5,
        ),
    )

    request = FarmerUpdateRequest()

    result = update_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=request,
    )

    assert result.preferred_language == "English"
    assert result.experience_years == 5


# ============================================================
# CLEAR EXPERIENCE
# ============================================================


def test_update_can_clear_experience(db):

    repository = FarmerRepository(db)

    user_id = uuid4()

    create_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=FarmerCreateRequest(
            preferred_language="English",
            experience_years=10,
        ),
    )

    request = FarmerUpdateRequest(
        experience_years=None,
    )

    result = update_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=request,
    )

    assert result.experience_years is None


# ============================================================
# UPDATE MISSING PROFILE
# ============================================================


def test_update_farmer_profile_not_found(db):

    repository = FarmerRepository(db)

    request = FarmerUpdateRequest(
        preferred_language="Telugu",
    )

    with pytest.raises(
        FarmerProfileNotFoundError,
    ):

        update_farmer_profile(
            repository=repository,
            user_id=uuid4(),
            request=request,
        )


# ============================================================
# UPDATE ONLY SUPPLIED FIELD
# ============================================================


def test_update_only_changes_supplied_field(db):

    repository = FarmerRepository(db)

    user_id = uuid4()

    create_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=FarmerCreateRequest(
            preferred_language="English",
            experience_years=15,
        ),
    )

    request = FarmerUpdateRequest(
        preferred_language="Telugu",
    )

    result = update_farmer_profile(
        repository=repository,
        user_id=user_id,
        request=request,
    )

    assert result.preferred_language == "Telugu"

    # Experience must remain unchanged.
    assert result.experience_years == 15


# ============================================================
# PROFILE INITIAL STATE
# ============================================================


def test_create_profile_initial_state(db):

    repository = FarmerRepository(db)

    result = create_farmer_profile(
        repository=repository,
        user_id=uuid4(),
        request=FarmerCreateRequest(),
    )

    assert result.profile_completion == PROFILE_INITIAL
    assert result.onboarding_completed is False