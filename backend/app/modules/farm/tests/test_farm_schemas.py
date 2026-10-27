from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.farm.schemas import (
    FarmCreateRequest,
    FarmUpdateRequest,
    FarmResponse,
)


# ============================================================
# FARM CREATE REQUEST
# ============================================================


def test_create_request_valid():

    request = FarmCreateRequest(
        farm_name="My Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Example Village",
        latitude=14.4426,
        longitude=79.9865,
        land_area=2.5,
        land_unit="Acres",
        soil_type="Clay",
        water_source="Borewell",
        water_availability="HIGH",
        irrigation_method="Drip",
        is_primary=True,
    )

    assert request.farm_name == "My Farm"
    assert request.state == "Andhra Pradesh"
    assert request.district == "Nellore"
    assert request.mandal == "Kavali"
    assert request.village == "Example Village"

    assert request.latitude == 14.4426
    assert request.longitude == 79.9865

    assert request.land_area == 2.5
    assert request.land_unit == "Acres"

    assert request.soil_type == "Clay"
    assert request.water_source == "Borewell"
    assert request.water_availability == "HIGH"
    assert request.irrigation_method == "Drip"

    assert request.is_primary is True


# ============================================================
# DEFAULT LAND UNIT
# ============================================================


def test_create_request_default_land_unit():

    request = FarmCreateRequest(
        farm_name="My Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Village",
        land_area=1.0,
    )

    assert request.land_unit == "Acres"


# ============================================================
# DEFAULT PRIMARY
# ============================================================


def test_create_request_default_primary():

    request = FarmCreateRequest(
        farm_name="My Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Village",
        land_area=1.0,
    )

    assert request.is_primary is False


# ============================================================
# STRING TRIMMING
# ============================================================


def test_create_request_trims_string_fields():

    request = FarmCreateRequest(
        farm_name="  My Farm  ",
        state="  Andhra Pradesh  ",
        district="  Nellore  ",
        mandal="  Kavali  ",
        village="  Village  ",
        land_area=1.0,
        land_unit="  Acres  ",
        soil_type="  Clay  ",
        water_source="  Borewell  ",
        water_availability="  HIGH  ",
        irrigation_method="  Drip  ",
    )

    assert request.farm_name == "My Farm"
    assert request.state == "Andhra Pradesh"
    assert request.district == "Nellore"
    assert request.mandal == "Kavali"
    assert request.village == "Village"

    assert request.land_unit == "Acres"
    assert request.soil_type == "Clay"
    assert request.water_source == "Borewell"
    assert request.water_availability == "HIGH"
    assert request.irrigation_method == "Drip"


# ============================================================
# EMPTY REQUIRED STRING
# ============================================================


@pytest.mark.parametrize(
    "field",
    [
        "farm_name",
        "state",
        "district",
        "mandal",
        "village",
    ],
)
def test_create_request_rejects_empty_required_string(
    field,
):

    data = {
        "farm_name": "My Farm",
        "state": "Andhra Pradesh",
        "district": "Nellore",
        "mandal": "Kavali",
        "village": "Village",
        "land_area": 1.0,
    }

    data[field] = "   "

    with pytest.raises(
        ValidationError,
    ):
        FarmCreateRequest(**data)


# ============================================================
# REQUIRED STRING TOO SHORT
# ============================================================


@pytest.mark.parametrize(
    "field",
    [
        "farm_name",
        "state",
        "district",
        "mandal",
        "village",
    ],
)
def test_create_request_rejects_short_required_string(
    field,
):

    data = {
        "farm_name": "My Farm",
        "state": "Andhra Pradesh",
        "district": "Nellore",
        "mandal": "Kavali",
        "village": "Village",
        "land_area": 1.0,
    }

    data[field] = "A"

    with pytest.raises(
        ValidationError,
    ):
        FarmCreateRequest(**data)


# ============================================================
# EMPTY OPTIONAL STRING
# ============================================================


@pytest.mark.parametrize(
    "field",
    [
        "land_unit",
        "soil_type",
        "water_source",
        "water_availability",
        "irrigation_method",
    ],
)
def test_create_request_rejects_empty_optional_string(
    field,
):

    data = {
        "farm_name": "My Farm",
        "state": "Andhra Pradesh",
        "district": "Nellore",
        "mandal": "Kavali",
        "village": "Village",
        "land_area": 1.0,
    }

    data[field] = "   "

    with pytest.raises(
        ValidationError,
    ):
        FarmCreateRequest(**data)


# ============================================================
# NULL OPTIONAL STRINGS
# ============================================================


def test_create_request_accepts_null_optional_fields():

    request = FarmCreateRequest(
        farm_name="My Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Village",
        land_area=1.0,
        soil_type=None,
        water_source=None,
        water_availability=None,
        irrigation_method=None,
    )

    assert request.soil_type is None
    assert request.water_source is None
    assert request.water_availability is None
    assert request.irrigation_method is None


# ============================================================
# LAND AREA
# ============================================================


def test_create_request_accepts_positive_land_area():

    request = FarmCreateRequest(
        farm_name="My Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Village",
        land_area=1.5,
    )

    assert request.land_area == 1.5


@pytest.mark.parametrize(
    "land_area",
    [
        0,
        -1,
        -0.5,
    ],
)
def test_create_request_rejects_invalid_land_area(
    land_area,
):

    with pytest.raises(
        ValidationError,
    ):
        FarmCreateRequest(
            farm_name="My Farm",
            state="Andhra Pradesh",
            district="Nellore",
            mandal="Kavali",
            village="Village",
            land_area=land_area,
        )


# ============================================================
# LATITUDE
# ============================================================


@pytest.mark.parametrize(
    "latitude",
    [
        -90,
        0,
        90,
    ],
)
def test_create_request_accepts_valid_latitude(
    latitude,
):

    request = FarmCreateRequest(
        farm_name="My Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Village",
        land_area=1.0,
        latitude=latitude,
    )

    assert request.latitude == latitude


@pytest.mark.parametrize(
    "latitude",
    [
        -90.1,
        90.1,
    ],
)
def test_create_request_rejects_invalid_latitude(
    latitude,
):

    with pytest.raises(
        ValidationError,
    ):
        FarmCreateRequest(
            farm_name="My Farm",
            state="Andhra Pradesh",
            district="Nellore",
            mandal="Kavali",
            village="Village",
            land_area=1.0,
            latitude=latitude,
        )


# ============================================================
# LONGITUDE
# ============================================================


@pytest.mark.parametrize(
    "longitude",
    [
        -180,
        0,
        180,
    ],
)
def test_create_request_accepts_valid_longitude(
    longitude,
):

    request = FarmCreateRequest(
        farm_name="My Farm",
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Village",
        land_area=1.0,
        longitude=longitude,
    )

    assert request.longitude == longitude


@pytest.mark.parametrize(
    "longitude",
    [
        -180.1,
        180.1,
    ],
)
def test_create_request_rejects_invalid_longitude(
    longitude,
):

    with pytest.raises(
        ValidationError,
    ):
        FarmCreateRequest(
            farm_name="My Farm",
            state="Andhra Pradesh",
            district="Nellore",
            mandal="Kavali",
            village="Village",
            land_area=1.0,
            longitude=longitude,
        )


# ============================================================
# UPDATE REQUEST
# ============================================================


def test_update_request_can_be_empty():

    request = FarmUpdateRequest()

    assert request.model_dump(
        exclude_unset=True,
    ) == {}


# ============================================================
# UPDATE REQUEST
# ============================================================


def test_update_request_valid():

    request = FarmUpdateRequest(
        farm_name="Updated Farm",
        land_area=3.0,
        soil_type="Black Soil",
        is_primary=True,
    )

    assert request.farm_name == "Updated Farm"
    assert request.land_area == 3.0
    assert request.soil_type == "Black Soil"
    assert request.is_primary is True


# ============================================================
# UPDATE REQUEST TRIMMING
# ============================================================


def test_update_request_trims_strings():

    request = FarmUpdateRequest(
        farm_name="  Updated Farm  ",
        state="  Andhra Pradesh  ",
        soil_type="  Clay  ",
    )

    assert request.farm_name == "Updated Farm"
    assert request.state == "Andhra Pradesh"
    assert request.soil_type == "Clay"


# ============================================================
# UPDATE REQUEST EXPLICIT NULL
# ============================================================


def test_update_request_can_clear_nullable_fields():

    request = FarmUpdateRequest(
        latitude=None,
        longitude=None,
        soil_type=None,
        water_source=None,
        water_availability=None,
        irrigation_method=None,
    )

    data = request.model_dump(
        exclude_unset=True,
    )

    assert "latitude" in data
    assert "longitude" in data
    assert "soil_type" in data
    assert "water_source" in data
    assert "water_availability" in data
    assert "irrigation_method" in data

    assert data["latitude"] is None
    assert data["longitude"] is None
    assert data["soil_type"] is None


# ============================================================
# UPDATE INVALID LAND AREA
# ============================================================


@pytest.mark.parametrize(
    "land_area",
    [
        0,
        -1,
    ],
)
def test_update_request_rejects_invalid_land_area(
    land_area,
):

    with pytest.raises(
        ValidationError,
    ):
        FarmUpdateRequest(
            land_area=land_area,
        )


# ============================================================
# UPDATE INVALID LATITUDE
# ============================================================


def test_update_request_rejects_invalid_latitude():

    with pytest.raises(
        ValidationError,
    ):
        FarmUpdateRequest(
            latitude=91,
        )


# ============================================================
# UPDATE INVALID LONGITUDE
# ============================================================


def test_update_request_rejects_invalid_longitude():

    with pytest.raises(
        ValidationError,
    ):
        FarmUpdateRequest(
            longitude=181,
        )


# ============================================================
# UPDATE INVALID STRING
# ============================================================


def test_update_request_rejects_empty_farm_name():

    with pytest.raises(
        ValidationError,
    ):
        FarmUpdateRequest(
            farm_name="   ",
        )


# ============================================================
# FARM RESPONSE
# ============================================================


def test_farm_response_from_attributes():

    farm_id = uuid4()
    farmer_id = uuid4()

    farm = type(
        "FarmObject",
        (),
        {
            "id": farm_id,
            "farmer_id": farmer_id,
            "farm_name": "My Farm",
            "state": "Andhra Pradesh",
            "district": "Nellore",
            "mandal": "Kavali",
            "village": "Village",
            "latitude": 14.4,
            "longitude": 79.9,
            "land_area": 2.0,
            "land_unit": "Acres",
            "soil_type": "Clay",
            "water_source": "Borewell",
            "water_availability": "HIGH",
            "irrigation_method": "Drip",
            "is_primary": True,
        },
    )()

    response = FarmResponse.model_validate(
        farm,
    )

    assert response.id == farm_id
    assert response.farmer_id == farmer_id
    assert response.farm_name == "My Farm"
    assert response.land_area == 2.0
    assert response.is_primary is True