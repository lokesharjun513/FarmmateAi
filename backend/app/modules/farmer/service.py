from uuid import UUID

from app.modules.farmer.models import Farmer
from app.modules.farmer.repository import FarmerRepository
from app.modules.farmer.schemas import (
    FarmerCreateRequest,
    FarmerUpdateRequest,
)
from app.shared.constants import PROFILE_INITIAL
from app.shared.exceptions import (
    FarmerProfileAlreadyExistsError,
    FarmerProfileNotFoundError,
)


# ============================================================
# CREATE FARMER PROFILE
# ============================================================


def create_farmer_profile(
    repository: FarmerRepository,
    user_id: UUID,
    request: FarmerCreateRequest,
) -> Farmer:
    """
    Create a farmer profile for an authenticated user.

    A user can have only one farmer profile.
    """

    # --------------------------------------------------------
    # Prevent duplicate farmer profiles.
    # --------------------------------------------------------

    existing_farmer = repository.get_by_user_id(
        user_id,
    )

    if existing_farmer:
        raise FarmerProfileAlreadyExistsError()

    # --------------------------------------------------------
    # Create farmer profile.
    # --------------------------------------------------------

    farmer = Farmer(
        user_id=user_id,
        preferred_language=request.preferred_language,
        experience_years=request.experience_years,
        profile_completion=PROFILE_INITIAL,
        onboarding_completed=False,
    )

    return repository.create(farmer)


# ============================================================
# GET FARMER PROFILE
# ============================================================


def get_farmer_profile(
    repository: FarmerRepository,
    user_id: UUID,
) -> Farmer:
    """
    Get the farmer profile belonging to the authenticated user.
    """

    farmer = repository.get_by_user_id(
        user_id,
    )

    if farmer is None:
        raise FarmerProfileNotFoundError()

    return farmer


# ============================================================
# UPDATE FARMER PROFILE
# ============================================================


def update_farmer_profile(
    repository: FarmerRepository,
    user_id: UUID,
    request: FarmerUpdateRequest,
) -> Farmer:
    """
    Update the farmer profile belonging to the authenticated user.

    Only fields explicitly supplied by the client are updated.
    """

    farmer = repository.get_by_user_id(
        user_id,
    )

    if farmer is None:
        raise FarmerProfileNotFoundError()

    # --------------------------------------------------------
    # Get only fields explicitly supplied by the client.
    #
    # This allows:
    #
    # {}                         → change nothing
    # {"preferred_language": ...} → update language
    # {"experience_years": 5}     → update experience
    # {"experience_years": null}  → clear experience
    # --------------------------------------------------------

    update_data = request.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(
            farmer,
            field,
            value,
        )

    # --------------------------------------------------------
    # Profile completion
    #
    # This is intentionally kept simple for now.
    #
    # Detailed onboarding completion rules should be handled
    # when we review the complete onboarding flow.
    # --------------------------------------------------------

    return repository.update(
        farmer,
    )