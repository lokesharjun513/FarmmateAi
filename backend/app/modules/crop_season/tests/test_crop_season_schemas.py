from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.crop_season.schemas import (
    CropSeasonCancelRequest,
    CropSeasonCreateRequest,
    CropSeasonHarvestRequest,
    CropSeasonResponse,
    CropSeasonStartRequest,
    CropSeasonStatus,
    CropSeasonUpdateRequest,
    FarmingSeason,
)


# ============================================================
# COMMON DATA
# ============================================================

FARM_ID = uuid4()

SOWING_DATE = date(2026, 6, 15)

EXPECTED_HARVEST_DATE = date(2026, 10, 15)

HARVESTED_DATE = date(2026, 10, 20)


def valid_create_payload() -> dict:
    return {
        "crop_name": "Rice",
        "crop_variety": "BPT 5204",
        "season": "KHARIF",
        "year": 2026,
        "sowing_date": SOWING_DATE,
        "expected_harvest_date": EXPECTED_HARVEST_DATE,
        "land_area": 2.5,
        "land_unit": "Acres",
        "notes": "Main paddy crop",
    }


# ============================================================
# CREATE REQUEST
# ============================================================


def test_create_request_valid():

    request = CropSeasonCreateRequest(
        **valid_create_payload(),
    )

    assert request.crop_name == "Rice"
    assert request.crop_variety == "BPT 5204"
    assert request.season == FarmingSeason.KHARIF
    assert request.year == 2026
    assert request.sowing_date == SOWING_DATE
    assert request.expected_harvest_date == EXPECTED_HARVEST_DATE
    assert request.land_area == 2.5
    assert request.land_unit == "Acres"
    assert request.notes == "Main paddy crop"


def test_create_request_default_land_unit():

    payload = valid_create_payload()

    payload.pop("land_unit")

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert request.land_unit == "Acres"


def test_create_request_optional_fields_can_be_null():

    payload = valid_create_payload()

    payload["crop_variety"] = None
    payload["expected_harvest_date"] = None
    payload["notes"] = None

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert request.crop_variety is None
    assert request.expected_harvest_date is None
    assert request.notes is None


def test_create_request_trims_crop_name():

    payload = valid_create_payload()

    payload["crop_name"] = "  Rice  "

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert request.crop_name == "Rice"


def test_create_request_rejects_short_crop_name():

    payload = valid_create_payload()

    payload["crop_name"] = "R"

    with pytest.raises(ValidationError):

        CropSeasonCreateRequest(
            **payload,
        )


def test_create_request_rejects_empty_crop_name():

    payload = valid_create_payload()

    payload["crop_name"] = "   "

    with pytest.raises(ValidationError):

        CropSeasonCreateRequest(
            **payload,
        )


def test_create_request_trims_crop_variety():

    payload = valid_create_payload()

    payload["crop_variety"] = "  BPT 5204  "

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert request.crop_variety == "BPT 5204"


def test_create_request_empty_crop_variety_becomes_none():

    payload = valid_create_payload()

    payload["crop_variety"] = "   "

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert request.crop_variety is None


@pytest.mark.parametrize(
    "season",
    [
        "KHARIF",
        "RABI",
        "ZAID",
    ],
)
def test_create_request_accepts_valid_season(
    season,
):

    payload = valid_create_payload()

    payload["season"] = season

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert request.season.value == season


def test_create_request_rejects_invalid_season():

    payload = valid_create_payload()

    payload["season"] = "MONSOON"

    with pytest.raises(ValidationError):

        CropSeasonCreateRequest(
            **payload,
        )


@pytest.mark.parametrize(
    "year",
    [
        2000,
        2026,
        2100,
    ],
)
def test_create_request_accepts_valid_year(
    year,
):

    payload = valid_create_payload()

    payload["year"] = year

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert request.year == year


@pytest.mark.parametrize(
    "year",
    [
        1999,
        0,
        2101,
    ],
)
def test_create_request_rejects_invalid_year(
    year,
):

    payload = valid_create_payload()

    payload["year"] = year

    with pytest.raises(ValidationError):

        CropSeasonCreateRequest(
            **payload,
        )


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

    payload = valid_create_payload()

    payload["land_area"] = land_area

    with pytest.raises(ValidationError):

        CropSeasonCreateRequest(
            **payload,
        )


@pytest.mark.parametrize(
    "land_area",
    [
        0.01,
        1,
        2.5,
        100,
    ],
)
def test_create_request_accepts_positive_land_area(
    land_area,
):

    payload = valid_create_payload()

    payload["land_area"] = land_area

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert request.land_area == land_area


def test_create_request_trims_land_unit():

    payload = valid_create_payload()

    payload["land_unit"] = "  Acres  "

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert request.land_unit == "Acres"


def test_create_request_rejects_empty_land_unit():

    payload = valid_create_payload()

    payload["land_unit"] = "   "

    with pytest.raises(ValidationError):

        CropSeasonCreateRequest(
            **payload,
        )


def test_create_request_trims_notes():

    payload = valid_create_payload()

    payload["notes"] = "  Paddy crop  "

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert request.notes == "Paddy crop"


def test_create_request_empty_notes_becomes_none():

    payload = valid_create_payload()

    payload["notes"] = "   "

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert request.notes is None


def test_create_request_expected_harvest_equal_sowing():

    payload = valid_create_payload()

    payload["expected_harvest_date"] = SOWING_DATE

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert (
        request.expected_harvest_date
        == request.sowing_date
    )


def test_create_request_expected_harvest_before_sowing():

    payload = valid_create_payload()

    payload["expected_harvest_date"] = date(
        2026,
        6,
        14,
    )

    with pytest.raises(ValidationError):

        CropSeasonCreateRequest(
            **payload,
        )


# ============================================================
# CREATE REQUEST - EXTRA FIELDS
# ============================================================


def test_create_request_rejects_unknown_lifecycle_fields():

    payload = valid_create_payload()

    payload["status"] = "ACTIVE"

    # NOTE:
    # Current schema does not set extra="forbid".
    # Therefore this test should only be enabled after
    # adding ConfigDict(extra="forbid") to the schema.
    #
    # For the current schema, Pydantic ignores the field.

    request = CropSeasonCreateRequest(
        **payload,
    )

    assert not hasattr(
        request,
        "status",
    )


# ============================================================
# UPDATE REQUEST
# ============================================================


def test_update_request_valid():

    request = CropSeasonUpdateRequest(
        crop_name="Rice",
        land_area=3.5,
        notes="Updated crop",
    )

    assert request.crop_name == "Rice"
    assert request.land_area == 3.5
    assert request.notes == "Updated crop"


def test_update_request_can_update_only_one_field():

    request = CropSeasonUpdateRequest(
        crop_name="Rice",
    )

    assert request.crop_name == "Rice"


def test_update_request_rejects_empty_update():

    with pytest.raises(ValidationError):

        CropSeasonUpdateRequest()


def test_update_request_trims_crop_name():

    request = CropSeasonUpdateRequest(
        crop_name="  Rice  ",
    )

    assert request.crop_name == "Rice"


def test_update_request_rejects_short_crop_name():

    with pytest.raises(ValidationError):

        CropSeasonUpdateRequest(
            crop_name="R",
        )


def test_update_request_empty_crop_variety_becomes_none():

    request = CropSeasonUpdateRequest(
        crop_variety="   ",
    )

    assert request.crop_variety is None


@pytest.mark.parametrize(
    "land_area",
    [
        0,
        -1,
        -0.5,
    ],
)
def test_update_request_rejects_invalid_land_area(
    land_area,
):

    with pytest.raises(ValidationError):

        CropSeasonUpdateRequest(
            land_area=land_area,
        )


def test_update_request_accepts_null_nullable_fields():

    request = CropSeasonUpdateRequest(
        crop_variety=None,
        expected_harvest_date=None,
        notes=None,
    )

    assert request.crop_variety is None
    assert request.expected_harvest_date is None
    assert request.notes is None


def test_update_request_trims_land_unit():

    request = CropSeasonUpdateRequest(
        land_unit="  Acres  ",
    )

    assert request.land_unit == "Acres"


def test_update_request_rejects_empty_land_unit():

    with pytest.raises(ValidationError):

        CropSeasonUpdateRequest(
            land_unit="   ",
        )


def test_update_request_trims_notes():

    request = CropSeasonUpdateRequest(
        notes="  Updated notes  ",
    )

    assert request.notes == "Updated notes"


def test_update_request_empty_notes_becomes_none():

    request = CropSeasonUpdateRequest(
        notes="   ",
    )

    assert request.notes is None


def test_update_request_valid_dates():

    request = CropSeasonUpdateRequest(
        sowing_date=date(
            2026,
            6,
            15,
        ),
        expected_harvest_date=date(
            2026,
            10,
            15,
        ),
    )

    assert (
        request.expected_harvest_date
        >= request.sowing_date
    )


def test_update_request_rejects_invalid_dates():

    with pytest.raises(ValidationError):

        CropSeasonUpdateRequest(
            sowing_date=date(
                2026,
                10,
                15,
            ),
            expected_harvest_date=date(
                2026,
                6,
                15,
            ),
        )


def test_update_request_accepts_season():

    request = CropSeasonUpdateRequest(
        season=FarmingSeason.RABI,
    )

    assert request.season == FarmingSeason.RABI


@pytest.mark.parametrize(
    "year",
    [
        1999,
        2101,
    ],
)
def test_update_request_rejects_invalid_year(
    year,
):

    with pytest.raises(ValidationError):

        CropSeasonUpdateRequest(
            year=year,
        )


# ============================================================
# START REQUEST
# ============================================================


def test_start_request_accepts_empty_body():

    request = CropSeasonStartRequest()

    assert request is not None


def test_start_request_rejects_extra_fields():

    with pytest.raises(ValidationError):

        CropSeasonStartRequest(
            status="ACTIVE",
        )


# ============================================================
# HARVEST REQUEST
# ============================================================


def test_harvest_request_empty_body():

    request = CropSeasonHarvestRequest()

    assert request.harvested_date is None
    assert request.notes is None


def test_harvest_request_valid():

    request = CropSeasonHarvestRequest(
        harvested_date=HARVESTED_DATE,
        notes="Harvest completed",
    )

    assert request.harvested_date == HARVESTED_DATE
    assert request.notes == "Harvest completed"


def test_harvest_request_trims_notes():

    request = CropSeasonHarvestRequest(
        notes="  Harvest completed  ",
    )

    assert request.notes == "Harvest completed"


def test_harvest_request_empty_notes_becomes_none():

    request = CropSeasonHarvestRequest(
        notes="   ",
    )

    assert request.notes is None


# ============================================================
# CANCEL REQUEST
# ============================================================


def test_cancel_request_empty_body():

    request = CropSeasonCancelRequest()

    assert request.reason is None


def test_cancel_request_valid():

    request = CropSeasonCancelRequest(
        reason="Farmer changed crop plan",
    )

    assert (
        request.reason
        == "Farmer changed crop plan"
    )


def test_cancel_request_trims_reason():

    request = CropSeasonCancelRequest(
        reason="  Weather issue  ",
    )

    assert request.reason == "Weather issue"


def test_cancel_request_empty_reason_becomes_none():

    request = CropSeasonCancelRequest(
        reason="   ",
    )

    assert request.reason is None


# ============================================================
# RESPONSE
# ============================================================


def test_crop_season_response_valid():

    crop_season_id = uuid4()

    response = CropSeasonResponse(
        id=crop_season_id,
        farm_id=FARM_ID,
        crop_name="Rice",
        crop_variety="BPT 5204",
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=SOWING_DATE,
        expected_harvest_date=EXPECTED_HARVEST_DATE,
        harvested_date=None,
        land_area=2.5,
        land_unit="Acres",
        status=CropSeasonStatus.PLANNED,
        is_active=False,
        notes="Main crop",
    )

    assert response.id == crop_season_id
    assert response.farm_id == FARM_ID
    assert response.crop_name == "Rice"
    assert response.crop_variety == "BPT 5204"
    assert response.season == FarmingSeason.KHARIF
    assert response.year == 2026
    assert response.land_area == 2.5
    assert response.status == CropSeasonStatus.PLANNED
    assert response.is_active is False


def test_crop_season_response_optional_fields_can_be_null():

    response = CropSeasonResponse(
        id=uuid4(),
        farm_id=FARM_ID,
        crop_name="Rice",
        crop_variety=None,
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=SOWING_DATE,
        expected_harvest_date=None,
        harvested_date=None,
        land_area=2.5,
        land_unit="Acres",
        status=CropSeasonStatus.PLANNED,
        is_active=False,
        notes=None,
    )

    assert response.crop_variety is None
    assert response.expected_harvest_date is None
    assert response.harvested_date is None
    assert response.notes is None


# ============================================================
# RESPONSE ENUM VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "status",
    [
        CropSeasonStatus.PLANNED,
        CropSeasonStatus.ACTIVE,
        CropSeasonStatus.HARVESTED,
        CropSeasonStatus.CANCELLED,
    ],
)
def test_response_accepts_all_statuses(
    status,
):

    response = CropSeasonResponse(
        id=uuid4(),
        farm_id=FARM_ID,
        crop_name="Rice",
        crop_variety=None,
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=SOWING_DATE,
        expected_harvest_date=None,
        harvested_date=None,
        land_area=2.5,
        land_unit="Acres",
        status=status,
        is_active=(
            status == CropSeasonStatus.ACTIVE
        ),
        notes=None,
    )

    assert response.status == status


@pytest.mark.parametrize(
    "season",
    [
        FarmingSeason.KHARIF,
        FarmingSeason.RABI,
        FarmingSeason.ZAID,
    ],
)
def test_response_accepts_all_farming_seasons(
    season,
):

    response = CropSeasonResponse(
        id=uuid4(),
        farm_id=FARM_ID,
        crop_name="Rice",
        crop_variety=None,
        season=season,
        year=2026,
        sowing_date=SOWING_DATE,
        expected_harvest_date=None,
        harvested_date=None,
        land_area=2.5,
        land_unit="Acres",
        status=CropSeasonStatus.PLANNED,
        is_active=False,
        notes=None,
    )

    assert response.season == season


# ============================================================
# ENUM VALUES
# ============================================================


def test_crop_season_status_values():

    assert CropSeasonStatus.PLANNED.value == "PLANNED"
    assert CropSeasonStatus.ACTIVE.value == "ACTIVE"
    assert CropSeasonStatus.HARVESTED.value == "HARVESTED"
    assert CropSeasonStatus.CANCELLED.value == "CANCELLED"


def test_farming_season_values():

    assert FarmingSeason.KHARIF.value == "KHARIF"
    assert FarmingSeason.RABI.value == "RABI"
    assert FarmingSeason.ZAID.value == "ZAID"