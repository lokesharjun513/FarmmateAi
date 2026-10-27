from datetime import date

import pytest

from sqlalchemy.exc import IntegrityError

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
    FarmingSeason,
)


# ============================================================
# HELPERS
# ============================================================


def crop_season_payload(
    **overrides,
) -> dict:
    """
    Return a valid CropSeason payload.

    farm_id is intentionally just a UUID because the SQLite
    test database used by conftest.py does not enforce
    PostgreSQL-style foreign key behavior by default.
    """

    from uuid import uuid4

    payload = {
        "farm_id": uuid4(),
        "crop_name": "Rice",
        "crop_variety": "BPT 5204",
        "land_area": 2.5,
        "land_unit": "Acres",
        "season": FarmingSeason.KHARIF,
        "year": 2026,
        "sowing_date": date(2026, 6, 15),
        "expected_harvest_date": date(2026, 10, 15),
        "harvested_date": None,
        "status": CropSeasonStatus.PLANNED,
        "is_active": False,
        "notes": "Test crop season",
    }

    payload.update(overrides)

    return payload


def create_crop_season(
    db,
    **overrides,
) -> CropSeason:

    crop_season = CropSeason(
        **crop_season_payload(
            **overrides,
        )
    )

    db.add(crop_season)
    db.commit()
    db.refresh(crop_season)

    return crop_season


# ============================================================
# ENUM TESTS
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


# ============================================================
# CREATE
# ============================================================


def test_create_crop_season(
    db,
):

    crop_season = create_crop_season(
        db,
    )

    assert crop_season.id is not None

    assert crop_season.crop_name == "Rice"
    assert crop_season.crop_variety == "BPT 5204"

    assert crop_season.land_area == 2.5
    assert crop_season.land_unit == "Acres"

    assert crop_season.season == FarmingSeason.KHARIF
    assert crop_season.year == 2026

    assert crop_season.sowing_date == date(
        2026,
        6,
        15,
    )

    assert crop_season.expected_harvest_date == date(
        2026,
        10,
        15,
    )

    assert crop_season.harvested_date is None

    assert crop_season.status == CropSeasonStatus.PLANNED

    assert crop_season.is_active is False

    assert crop_season.notes == "Test crop season"


# ============================================================
# PRIMARY KEY
# ============================================================


def test_crop_season_generates_unique_id(
    db,
):

    crop_1 = create_crop_season(
        db,
        crop_name="Rice",
    )

    crop_2 = create_crop_season(
        db,
        crop_name="Maize",
    )

    assert crop_1.id is not None
    assert crop_2.id is not None

    assert crop_1.id != crop_2.id


# ============================================================
# DEFAULT LAND UNIT
# ============================================================


def test_land_unit_default(
    db,
):

    from uuid import uuid4

    crop_season = CropSeason(
        farm_id=uuid4(),
        crop_name="Rice",
        land_area=2.0,
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 15),
    )

    db.add(crop_season)
    db.commit()
    db.refresh(crop_season)

    assert crop_season.land_unit == "Acres"


# ============================================================
# DEFAULT STATUS
# ============================================================


def test_status_default(
    db,
):

    from uuid import uuid4

    crop_season = CropSeason(
        farm_id=uuid4(),
        crop_name="Rice",
        land_area=2.0,
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 15),
    )

    db.add(crop_season)
    db.commit()
    db.refresh(crop_season)

    assert crop_season.status == CropSeasonStatus.PLANNED


# ============================================================
# DEFAULT ACTIVE FLAG
# ============================================================


def test_is_active_default(
    db,
):

    from uuid import uuid4

    crop_season = CropSeason(
        farm_id=uuid4(),
        crop_name="Rice",
        land_area=2.0,
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 15),
    )

    db.add(crop_season)
    db.commit()
    db.refresh(crop_season)

    assert crop_season.is_active is False


# ============================================================
# OPTIONAL FIELDS
# ============================================================


def test_optional_fields_can_be_null(
    db,
):

    crop_season = create_crop_season(
        db,
        crop_variety=None,
        expected_harvest_date=None,
        harvested_date=None,
        notes=None,
    )

    assert crop_season.crop_variety is None
    assert crop_season.expected_harvest_date is None
    assert crop_season.harvested_date is None
    assert crop_season.notes is None


# ============================================================
# ACTIVE CROP
# ============================================================


def test_active_crop(
    db,
):

    crop_season = create_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    assert crop_season.status == CropSeasonStatus.ACTIVE
    assert crop_season.is_active is True


# ============================================================
# HARVESTED CROP
# ============================================================


def test_harvested_crop(
    db,
):

    crop_season = create_crop_season(
        db,
        status=CropSeasonStatus.HARVESTED,
        is_active=False,
        harvested_date=date(
            2026,
            10,
            10,
        ),
    )

    assert crop_season.status == CropSeasonStatus.HARVESTED
    assert crop_season.is_active is False

    assert crop_season.harvested_date == date(
        2026,
        10,
        10,
    )


# ============================================================
# CANCELLED CROP
# ============================================================


def test_cancelled_crop(
    db,
):

    crop_season = create_crop_season(
        db,
        status=CropSeasonStatus.CANCELLED,
        is_active=False,
    )

    assert crop_season.status == CropSeasonStatus.CANCELLED
    assert crop_season.is_active is False


# ============================================================
# LAND AREA CONSTRAINT
# ============================================================


@pytest.mark.parametrize(
    "land_area",
    [
        0,
        -1,
        -0.5,
    ],
)
def test_land_area_must_be_positive(
    db,
    land_area,
):

    crop_season = CropSeason(
        **crop_season_payload(
            land_area=land_area,
        )
    )

    db.add(crop_season)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


# ============================================================
# YEAR CONSTRAINT
# ============================================================


@pytest.mark.parametrize(
    "year",
    [
        1999,
        1900,
        0,
    ],
)
def test_year_must_be_at_least_2000(
    db,
    year,
):

    crop_season = CropSeason(
        **crop_season_payload(
            year=year,
        )
    )

    db.add(crop_season)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


# ============================================================
# EXPECTED HARVEST DATE CONSTRAINT
# ============================================================


def test_expected_harvest_date_cannot_be_before_sowing_date(
    db,
):

    crop_season = CropSeason(
        **crop_season_payload(
            sowing_date=date(
                2026,
                6,
                15,
            ),
            expected_harvest_date=date(
                2026,
                6,
                10,
            ),
        )
    )

    db.add(crop_season)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


# ============================================================
# EXPECTED HARVEST DATE CAN EQUAL SOWING DATE
# ============================================================


def test_expected_harvest_date_can_equal_sowing_date(
    db,
):

    crop_season = create_crop_season(
        db,
        sowing_date=date(
            2026,
            6,
            15,
        ),
        expected_harvest_date=date(
            2026,
            6,
            15,
        ),
    )

    assert (
        crop_season.expected_harvest_date
        == crop_season.sowing_date
    )


# ============================================================
# HARVESTED DATE CONSTRAINT
# ============================================================


def test_harvested_date_cannot_be_before_sowing_date(
    db,
):

    crop_season = CropSeason(
        **crop_season_payload(
            sowing_date=date(
                2026,
                6,
                15,
            ),
            harvested_date=date(
                2026,
                6,
                10,
            ),
        )
    )

    db.add(crop_season)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


# ============================================================
# HARVESTED DATE CAN EQUAL SOWING DATE
# ============================================================


def test_harvested_date_can_equal_sowing_date(
    db,
):

    crop_season = create_crop_season(
        db,
        sowing_date=date(
            2026,
            6,
            15,
        ),
        harvested_date=date(
            2026,
            6,
            15,
        ),
    )

    assert (
        crop_season.harvested_date
        == crop_season.sowing_date
    )


# ============================================================
# ALL FARMING SEASONS
# ============================================================


@pytest.mark.parametrize(
    "season",
    [
        FarmingSeason.KHARIF,
        FarmingSeason.RABI,
        FarmingSeason.ZAID,
    ],
)
def test_all_farming_seasons(
    db,
    season,
):

    crop_season = create_crop_season(
        db,
        season=season,
    )

    assert crop_season.season == season


# ============================================================
# ALL CROP STATUSES
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
def test_all_crop_statuses(
    db,
    status,
):

    is_active = (
        status == CropSeasonStatus.ACTIVE
    )

    harvested_date = (
        date(2026, 10, 10)
        if status == CropSeasonStatus.HARVESTED
        else None
    )

    crop_season = create_crop_season(
        db,
        status=status,
        is_active=is_active,
        harvested_date=harvested_date,
    )

    assert crop_season.status == status
    assert crop_season.is_active == is_active


# ============================================================
# UPDATE
# ============================================================


def test_update_crop_season(
    db,
):

    crop_season = create_crop_season(
        db,
    )

    crop_season.crop_name = "Maize"
    crop_season.crop_variety = "Hybrid Maize"
    crop_season.land_area = 3.5
    crop_season.season = FarmingSeason.RABI
    crop_season.year = 2027

    db.commit()
    db.refresh(crop_season)

    assert crop_season.crop_name == "Maize"
    assert crop_season.crop_variety == "Hybrid Maize"
    assert crop_season.land_area == 3.5
    assert crop_season.season == FarmingSeason.RABI
    assert crop_season.year == 2027


# ============================================================
# UPDATE STATUS
# ============================================================


def test_update_status_to_active(
    db,
):

    crop_season = create_crop_season(
        db,
    )

    crop_season.status = CropSeasonStatus.ACTIVE
    crop_season.is_active = True

    db.commit()
    db.refresh(crop_season)

    assert crop_season.status == CropSeasonStatus.ACTIVE
    assert crop_season.is_active is True


# ============================================================
# UPDATE STATUS TO HARVESTED
# ============================================================


def test_update_status_to_harvested(
    db,
):

    crop_season = create_crop_season(
        db,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    crop_season.status = CropSeasonStatus.HARVESTED
    crop_season.is_active = False
    crop_season.harvested_date = date(
        2026,
        10,
        10,
    )

    db.commit()
    db.refresh(crop_season)

    assert (
        crop_season.status
        == CropSeasonStatus.HARVESTED
    )

    assert crop_season.is_active is False

    assert crop_season.harvested_date == date(
        2026,
        10,
        10,
    )


# ============================================================
# DELETE
# ============================================================


def test_delete_crop_season(
    db,
):

    crop_season = create_crop_season(
        db,
    )

    crop_season_id = crop_season.id

    db.delete(crop_season)
    db.commit()

    result = (
        db.query(CropSeason)
        .filter(
            CropSeason.id == crop_season_id,
        )
        .first()
    )

    assert result is None


# ============================================================
# TIMESTAMP MIXIN
# ============================================================


def test_timestamp_fields_are_created(
    db,
):

    crop_season = create_crop_season(
        db,
    )

    assert crop_season.created_at is not None
    assert crop_season.updated_at is not None


# ============================================================
# SAME FARM CAN HAVE MULTIPLE CROP SEASONS
# ============================================================


def test_same_farm_can_have_multiple_crop_seasons(
    db,
):

    from uuid import uuid4

    farm_id = uuid4()

    crop_1 = create_crop_season(
        db,
        farm_id=farm_id,
        crop_name="Rice",
    )

    crop_2 = create_crop_season(
        db,
        farm_id=farm_id,
        crop_name="Blackgram",
    )

    assert crop_1.farm_id == farm_id
    assert crop_2.farm_id == farm_id

    assert crop_1.id != crop_2.id


# ============================================================
# MULTIPLE ACTIVE CROPS ARE ALLOWED
# ============================================================


def test_multiple_active_crops_can_exist_for_same_farm(
    db,
):

    from uuid import uuid4

    farm_id = uuid4()

    crop_1 = create_crop_season(
        db,
        farm_id=farm_id,
        crop_name="Rice",
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    crop_2 = create_crop_season(
        db,
        farm_id=farm_id,
        crop_name="Blackgram",
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    active_crops = (
        db.query(CropSeason)
        .filter(
            CropSeason.farm_id == farm_id,
            CropSeason.status
            == CropSeasonStatus.ACTIVE,
            CropSeason.is_active.is_(True),
        )
        .all()
    )

    assert len(active_crops) == 2

    assert crop_1 in active_crops
    assert crop_2 in active_crops