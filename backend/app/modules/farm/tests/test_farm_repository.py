from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.farm.models import Farm
from app.modules.farm.repository import FarmRepository


# ============================================================
# HELPERS
# ============================================================


def create_farm(
    db,
    *,
    farmer_id=None,
    farm_name="Main Farm",
    is_primary=False,
):
    """
    Create and persist a real Farm for repository tests.
    """

    farm = Farm(
        farmer_id=farmer_id or uuid4(),
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

    db.add(farm)
    db.commit()
    db.refresh(farm)

    return farm


# ============================================================
# GET BY ID
# ============================================================


def test_get_by_id(db):

    farm = create_farm(db)

    repository = FarmRepository(db)

    result = repository.get_by_id(
        farm.id,
    )

    assert result is not None
    assert result.id == farm.id
    assert result.farm_name == "Main Farm"


# ============================================================
# GET BY ID NOT FOUND
# ============================================================


def test_get_by_id_not_found(db):

    repository = FarmRepository(db)

    result = repository.get_by_id(
        uuid4(),
    )

    assert result is None


# ============================================================
# GET BY ID + FARMER
# ============================================================


def test_get_by_id_and_farmer(db):

    farmer_id = uuid4()

    farm = create_farm(
        db,
        farmer_id=farmer_id,
    )

    repository = FarmRepository(db)

    result = repository.get_by_id_and_farmer(
        farm_id=farm.id,
        farmer_id=farmer_id,
    )

    assert result is not None
    assert result.id == farm.id
    assert result.farmer_id == farmer_id


# ============================================================
# GET BY ID + WRONG FARMER
# ============================================================


def test_get_by_id_and_farmer_wrong_farmer(db):

    owner_id = uuid4()
    other_farmer_id = uuid4()

    farm = create_farm(
        db,
        farmer_id=owner_id,
    )

    repository = FarmRepository(db)

    result = repository.get_by_id_and_farmer(
        farm_id=farm.id,
        farmer_id=other_farmer_id,
    )

    assert result is None


# ============================================================
# GET ALL FARMS
# ============================================================


def test_get_all_by_farmer(db):

    farmer_id = uuid4()

    farm_one = create_farm(
        db,
        farmer_id=farmer_id,
        farm_name="Farm One",
    )

    farm_two = create_farm(
        db,
        farmer_id=farmer_id,
        farm_name="Farm Two",
    )

    repository = FarmRepository(db)

    result = repository.get_all_by_farmer(
        farmer_id,
    )

    assert len(result) == 2

    result_ids = {
        farm.id
        for farm in result
    }

    assert farm_one.id in result_ids
    assert farm_two.id in result_ids


# ============================================================
# GET ALL FARMS DOES NOT RETURN OTHER FARMER FARMS
# ============================================================


def test_get_all_by_farmer_isolated(db):

    farmer_id = uuid4()
    other_farmer_id = uuid4()

    farm_one = create_farm(
        db,
        farmer_id=farmer_id,
        farm_name="My Farm",
    )

    create_farm(
        db,
        farmer_id=other_farmer_id,
        farm_name="Other Farm",
    )

    repository = FarmRepository(db)

    result = repository.get_all_by_farmer(
        farmer_id,
    )

    assert len(result) == 1
    assert result[0].id == farm_one.id


# ============================================================
# PRIMARY FARM
# ============================================================


def test_create_primary_farm(db):

    farmer_id = uuid4()

    farm = Farm(
        farmer_id=farmer_id,
        farm_name="Primary Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Example Village",
        land_area=3.0,
        land_unit="Acres",
        is_primary=True,
    )

    repository = FarmRepository(db)

    result = repository.create(
        farm,
    )

    assert result.is_primary is True


# ============================================================
# ONLY ONE PRIMARY FARM
# ============================================================


def test_only_one_primary_farm(db):

    farmer_id = uuid4()

    first = create_farm(
        db,
        farmer_id=farmer_id,
        farm_name="First Farm",
        is_primary=True,
    )

    second = create_farm(
        db,
        farmer_id=farmer_id,
        farm_name="Second Farm",
        is_primary=True,
    )

    repository = FarmRepository(db)

    farms = repository.get_all_by_farmer(
        farmer_id,
    )

    primary_farms = [
        farm
        for farm in farms
        if farm.is_primary
    ]

    assert len(primary_farms) == 1
    assert primary_farms[0].id == second.id

    db.refresh(first)

    assert first.is_primary is False


# ============================================================
# PRIMARY FARM DOES NOT AFFECT OTHER FARMERS
# ============================================================


def test_primary_farm_isolated_between_farmers(db):

    farmer_one = uuid4()
    farmer_two = uuid4()

    first = create_farm(
        db,
        farmer_id=farmer_one,
        farm_name="Farmer One Farm",
        is_primary=True,
    )

    second = create_farm(
        db,
        farmer_id=farmer_two,
        farm_name="Farmer Two Farm",
        is_primary=True,
    )

    db.refresh(first)
    db.refresh(second)

    assert first.is_primary is True
    assert second.is_primary is True


# ============================================================
# UPDATE FARM
# ============================================================


def test_update_farm(db):

    farm = create_farm(
        db,
        farm_name="Old Farm Name",
    )

    repository = FarmRepository(db)

    farm.farm_name = "Updated Farm Name"
    farm.land_area = 5.0

    result = repository.update(
        farm,
    )

    assert result.farm_name == "Updated Farm Name"
    assert result.land_area == 5.0


# ============================================================
# UPDATE PERSISTS
# ============================================================


def test_update_farm_persists(db):

    farm = create_farm(
        db,
        farm_name="Original Farm",
    )

    repository = FarmRepository(db)

    farm.farm_name = "Updated Farm"

    repository.update(
        farm,
    )

    db.expire_all()

    result = repository.get_by_id(
        farm.id,
    )

    assert result is not None
    assert result.farm_name == "Updated Farm"


# ============================================================
# UPDATE PRIMARY FARM
# ============================================================


def test_update_primary_farm(db):

    farmer_id = uuid4()

    first = create_farm(
        db,
        farmer_id=farmer_id,
        farm_name="First Farm",
        is_primary=True,
    )

    second = create_farm(
        db,
        farmer_id=farmer_id,
        farm_name="Second Farm",
        is_primary=False,
    )

    repository = FarmRepository(db)

    second.is_primary = True

    result = repository.update(
        second,
    )

    assert result.is_primary is True

    db.refresh(first)

    assert first.is_primary is False


# ============================================================
# SET PRIMARY DIRECTLY
# ============================================================


def test_set_primary(db):

    farmer_id = uuid4()

    first = create_farm(
        db,
        farmer_id=farmer_id,
        farm_name="First Farm",
        is_primary=True,
    )

    second = create_farm(
        db,
        farmer_id=farmer_id,
        farm_name="Second Farm",
        is_primary=False,
    )

    repository = FarmRepository(db)

    repository.set_primary(
        second,
    )

    db.commit()
    db.refresh(first)
    db.refresh(second)

    assert first.is_primary is False
    assert second.is_primary is True


def test_set_primary_does_not_affect_other_farmers(db):

    farmer_one = uuid4()
    farmer_two = uuid4()

    first = create_farm(
        db,
        farmer_id=farmer_one,
        farm_name="Farmer One First",
        is_primary=True,
    )

    second = create_farm(
        db,
        farmer_id=farmer_one,
        farm_name="Farmer One Second",
        is_primary=False,
    )

    other = create_farm(
        db,
        farmer_id=farmer_two,
        farm_name="Farmer Two Primary",
        is_primary=True,
    )

    repository = FarmRepository(db)

    repository.set_primary(
        second,
    )

    db.commit()
    db.refresh(first)
    db.refresh(second)
    db.refresh(other)

    assert first.is_primary is False
    assert second.is_primary is True
    assert other.is_primary is True


# ============================================================
# DELETE FARM
# ============================================================


def test_delete_farm(db):

    farm = create_farm(db)

    repository = FarmRepository(db)

    repository.delete(
        farm,
    )

    result = repository.get_by_id(
        farm.id,
    )

    assert result is None


# ============================================================
# DELETE DOES NOT AFFECT OTHER FARM
# ============================================================


def test_delete_farm_does_not_delete_other_farm(db):

    farmer_id = uuid4()

    first = create_farm(
        db,
        farmer_id=farmer_id,
        farm_name="First Farm",
    )

    second = create_farm(
        db,
        farmer_id=farmer_id,
        farm_name="Second Farm",
    )

    repository = FarmRepository(db)

    repository.delete(
        first,
    )

    result = repository.get_by_id(
        second.id,
    )

    assert result is not None
    assert result.farm_name == "Second Farm"


# ============================================================
# DIFFERENT FARMERS CAN HAVE PRIMARY FARMS
# ============================================================


def test_different_farmers_can_have_primary_farms(db):

    farmer_one = uuid4()
    farmer_two = uuid4()

    first = create_farm(
        db,
        farmer_id=farmer_one,
        farm_name="Farmer One Primary",
        is_primary=True,
    )

    second = create_farm(
        db,
        farmer_id=farmer_two,
        farm_name="Farmer Two Primary",
        is_primary=True,
    )

    assert first.is_primary is True
    assert second.is_primary is True


# ============================================================
# EMPTY FARM LIST
# ============================================================


def test_get_all_by_farmer_empty(db):

    repository = FarmRepository(db)

    result = repository.get_all_by_farmer(
        uuid4(),
    )

    assert result == []