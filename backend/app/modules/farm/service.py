from uuid import UUID

from app.modules.farm.models import Farm
from app.modules.farm.repository import FarmRepository
from app.modules.farm.schemas import (
    FarmCreateRequest,
    FarmUpdateRequest,
)

from app.shared.exceptions import (
    FarmNotFoundError,
)


# ============================================================
# CREATE FARM
# ============================================================


def create_farm(
    repository: FarmRepository,
    farmer_id: UUID,
    request: FarmCreateRequest,
) -> Farm:
    """
    Create a farm belonging to the specified farmer.

    If the new farm is marked as primary, the repository will
    ensure that it becomes the farmer's only primary farm.
    """

    farm = Farm(
        farmer_id=farmer_id,
        **request.model_dump(),
    )

    return repository.create(farm)


# ============================================================
# GET FARM
# ============================================================


def get_farm(
    repository: FarmRepository,
    farm_id: UUID,
    farmer_id: UUID,
) -> Farm:
    """
    Retrieve a farm only if it belongs to the specified farmer.
    """

    farm = repository.get_by_id_and_farmer(
        farm_id=farm_id,
        farmer_id=farmer_id,
    )

    if farm is None:
        raise FarmNotFoundError()

    return farm


# ============================================================
# LIST FARMS
# ============================================================


def list_farms(
    repository: FarmRepository,
    farmer_id: UUID,
) -> list[Farm]:
    """
    Return all farms belonging to a farmer.
    """

    return repository.get_all_by_farmer(
        farmer_id,
    )


# ============================================================
# UPDATE FARM
# ============================================================


def update_farm(
    repository: FarmRepository,
    farm: Farm,
    request: FarmUpdateRequest,
) -> Farm:
    """
    Update an existing farm.

    Fields explicitly supplied by the client are updated,
    including explicit None values for nullable fields.
    """

    update_data = request.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(
            farm,
            field,
            value,
        )

    return repository.update(
        farm,
    )


# ============================================================
# DELETE FARM
# ============================================================


def delete_farm(
    repository: FarmRepository,
    farm: Farm,
) -> None:
    """
    Delete a farm.

    The repository performs the database deletion.
    """

    repository.delete(
        farm,
    )