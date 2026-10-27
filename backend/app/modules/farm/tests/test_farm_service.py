from uuid import uuid4

import pytest

from app.modules.farm.models import Farm
from app.modules.farm.schemas import (
    FarmCreateRequest,
    FarmUpdateRequest,
)
from app.modules.farm.service import (
    create_farm,
    delete_farm,
    get_farm,
    list_farms,
    update_farm,
)
from app.shared.exceptions import FarmNotFoundError


# ============================================================
# TEST DATA
# ============================================================


def create_request(
    farm_name: str = "Test Farm",
    is_primary: bool = False,
) -> FarmCreateRequest:

    return FarmCreateRequest(
        farm_name=farm_name,
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Example Village",
        latitude=14.9167,
        longitude=79.9944,
        land_area=2.5,
        land_unit="Acres",
        soil_type="Clay",
        water_source="Borewell",
        water_availability="HIGH",
        irrigation_method="Drip",
        is_primary=is_primary,
    )


# ============================================================
# FAKE REPOSITORY
# ============================================================


class FakeFarmRepository:

    def __init__(self):
        self.farms: list[Farm] = []
        self.created = False
        self.updated = False
        self.deleted = False

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    def create(
        self,
        farm: Farm,
    ) -> Farm:

        self.farms.append(farm)
        self.created = True

        return farm

    # --------------------------------------------------------
    # GET BY ID + FARMER
    # --------------------------------------------------------

    def get_by_id_and_farmer(
        self,
        farm_id,
        farmer_id,
    ) -> Farm | None:

        for farm in self.farms:

            if (
                farm.id == farm_id
                and farm.farmer_id == farmer_id
            ):
                return farm

        return None

    # --------------------------------------------------------
    # GET ALL
    # --------------------------------------------------------

    def get_all_by_farmer(
        self,
        farmer_id,
    ) -> list[Farm]:

        return [
            farm
            for farm in self.farms
            if farm.farmer_id == farmer_id
        ]

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    def update(
        self,
        farm: Farm,
    ) -> Farm:

        self.updated = True

        return farm

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    def delete(
        self,
        farm: Farm,
    ) -> None:

        self.farms.remove(farm)
        self.deleted = True


# ============================================================
# CREATE FARM
# ============================================================


def test_create_farm():

    repository = FakeFarmRepository()

    farmer_id = uuid4()

    request = create_request(
        farm_name="My Farm",
    )

    result = create_farm(
        repository=repository,
        farmer_id=farmer_id,
        request=request,
    )

    assert result.farmer_id == farmer_id
    assert result.farm_name == "My Farm"
    assert result.state == "Andhra Pradesh"
    assert result.district == "Nellore"
    assert result.land_area == 2.5

    assert repository.created is True
    assert result in repository.farms


# ============================================================
# CREATE PRIMARY FARM
# ============================================================


def test_create_primary_farm():

    repository = FakeFarmRepository()

    farmer_id = uuid4()

    request = create_request(
        farm_name="Primary Farm",
        is_primary=True,
    )

    result = create_farm(
        repository=repository,
        farmer_id=farmer_id,
        request=request,
    )

    assert result.is_primary is True
    assert repository.created is True


# ============================================================
# GET FARM
# ============================================================


def test_get_farm():

    repository = FakeFarmRepository()

    farmer_id = uuid4()
    farm_id = uuid4()

    farm = Farm(
        id=farm_id,
        farmer_id=farmer_id,
        farm_name="Test Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Example Village",
        land_area=2.0,
        land_unit="Acres",
    )

    repository.farms.append(farm)

    result = get_farm(
        repository=repository,
        farm_id=farm_id,
        farmer_id=farmer_id,
    )

    assert result is farm


# ============================================================
# GET FARM - NOT FOUND
# ============================================================


def test_get_farm_not_found():

    repository = FakeFarmRepository()

    with pytest.raises(FarmNotFoundError):

        get_farm(
            repository=repository,
            farm_id=uuid4(),
            farmer_id=uuid4(),
        )


# ============================================================
# FARM OWNERSHIP IS ENFORCED
# ============================================================


def test_get_farm_wrong_farmer():

    repository = FakeFarmRepository()

    real_farmer_id = uuid4()
    wrong_farmer_id = uuid4()
    farm_id = uuid4()

    farm = Farm(
        id=farm_id,
        farmer_id=real_farmer_id,
        farm_name="Private Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Example Village",
        land_area=2.0,
        land_unit="Acres",
    )

    repository.farms.append(farm)

    with pytest.raises(FarmNotFoundError):

        get_farm(
            repository=repository,
            farm_id=farm_id,
            farmer_id=wrong_farmer_id,
        )


# ============================================================
# LIST FARMS
# ============================================================


def test_list_farms():

    repository = FakeFarmRepository()

    farmer_id = uuid4()

    farm_one = Farm(
        id=uuid4(),
        farmer_id=farmer_id,
        farm_name="Farm One",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Village One",
        land_area=2.0,
        land_unit="Acres",
    )

    farm_two = Farm(
        id=uuid4(),
        farmer_id=farmer_id,
        farm_name="Farm Two",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Village Two",
        land_area=3.0,
        land_unit="Acres",
    )

    repository.farms.extend(
        [
            farm_one,
            farm_two,
        ]
    )

    result = list_farms(
        repository=repository,
        farmer_id=farmer_id,
    )

    assert len(result) == 2
    assert farm_one in result
    assert farm_two in result


# ============================================================
# LIST FARMS ISOLATION
# ============================================================


def test_list_farms_only_returns_farmer_farms():

    repository = FakeFarmRepository()

    farmer_one = uuid4()
    farmer_two = uuid4()

    farm_one = Farm(
        id=uuid4(),
        farmer_id=farmer_one,
        farm_name="Farmer One Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Village One",
        land_area=2.0,
        land_unit="Acres",
    )

    farm_two = Farm(
        id=uuid4(),
        farmer_id=farmer_two,
        farm_name="Farmer Two Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Village Two",
        land_area=3.0,
        land_unit="Acres",
    )

    repository.farms.extend(
        [
            farm_one,
            farm_two,
        ]
    )

    result = list_farms(
        repository=repository,
        farmer_id=farmer_one,
    )

    assert len(result) == 1
    assert result[0] is farm_one


# ============================================================
# UPDATE FARM
# ============================================================


def test_update_farm():

    repository = FakeFarmRepository()

    farmer_id = uuid4()
    farm_id = uuid4()

    farm = Farm(
        id=farm_id,
        farmer_id=farmer_id,
        farm_name="Old Farm Name",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Example Village",
        land_area=2.0,
        land_unit="Acres",
    )

    request = FarmUpdateRequest(
        farm_name="Updated Farm",
        land_area=5.0,
    )

    result = update_farm(
        repository=repository,
        farm=farm,
        request=request,
    )

    assert result is farm
    assert result.farm_name == "Updated Farm"
    assert result.land_area == 5.0

    assert repository.updated is True


# ============================================================
# UPDATE ONLY SUPPLIED FIELDS
# ============================================================


def test_update_farm_only_changes_supplied_fields():

    repository = FakeFarmRepository()

    farmer_id = uuid4()

    farm = Farm(
        id=uuid4(),
        farmer_id=farmer_id,
        farm_name="Original Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Example Village",
        land_area=2.0,
        land_unit="Acres",
    )

    request = FarmUpdateRequest(
        farm_name="New Farm Name",
    )

    update_farm(
        repository=repository,
        farm=farm,
        request=request,
    )

    assert farm.farm_name == "New Farm Name"
    assert farm.land_area == 2.0
    assert farm.state == "Andhra Pradesh"


# ============================================================
# UPDATE NULLABLE FIELDS
# ============================================================


def test_update_farm_can_clear_nullable_fields():

    repository = FakeFarmRepository()

    farm = Farm(
        id=uuid4(),
        farmer_id=uuid4(),
        farm_name="Test Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Example Village",
        land_area=2.0,
        land_unit="Acres",
        soil_type="Clay",
        water_source="Borewell",
    )

    request = FarmUpdateRequest(
        soil_type=None,
        water_source=None,
    )

    update_farm(
        repository=repository,
        farm=farm,
        request=request,
    )

    assert farm.soil_type is None
    assert farm.water_source is None


# ============================================================
# DELETE FARM
# ============================================================


def test_delete_farm():

    repository = FakeFarmRepository()

    farm = Farm(
        id=uuid4(),
        farmer_id=uuid4(),
        farm_name="Delete Me",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Example Village",
        land_area=2.0,
        land_unit="Acres",
    )

    repository.farms.append(farm)

    delete_farm(
        repository=repository,
        farm=farm,
    )

    assert repository.deleted is True
    assert farm not in repository.farms