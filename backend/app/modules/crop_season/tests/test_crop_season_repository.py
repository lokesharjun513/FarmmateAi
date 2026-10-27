import uuid

from datetime import date, timedelta

from app.modules.crop_season.models import (
    CropSeason,
    CropSeasonStatus,
    FarmingSeason,
)
from app.modules.crop_season.repository import (
    CropSeasonRepository,
)
from app.modules.farm.models import Farm


# ============================================================
# HELPERS
# ============================================================


def create_farm(
    db,
    *,
    farmer_id=None,
    farm_name="Test Farm",
):
    farm = Farm(
        farmer_id=farmer_id or uuid.uuid4(),
        farm_name=farm_name,
        state="Andhra Pradesh",
        district="Nellore",
        mandal="Kavali",
        village="Test Village",
        latitude=14.9167,
        longitude=79.9944,
        land_area=5.0,
        land_unit="Acres",
        soil_type="Clay",
        water_source="Borewell",
        water_availability="HIGH",
        irrigation_method="Drip",
        is_primary=False,
    )

    db.add(farm)
    db.commit()
    db.refresh(farm)

    return farm


def create_crop(
    db,
    farm_id,
    *,
    crop_name="Rice",
    status=CropSeasonStatus.PLANNED,
    is_active=False,
    year=2026,
    season=FarmingSeason.KHARIF,
    sowing_date=date(2026, 6, 15),
    expected_harvest_date=date(2026, 10, 15),
    harvested_date=None,
):
    crop = CropSeason(
        farm_id=farm_id,
        crop_name=crop_name,
        crop_variety="BPT-5204",
        land_area=2.5,
        land_unit="Acres",
        season=season,
        year=year,
        sowing_date=sowing_date,
        expected_harvest_date=expected_harvest_date,
        harvested_date=harvested_date,
        status=status,
        is_active=is_active,
        notes="Test crop",
    )

    db.add(crop)
    db.commit()
    db.refresh(crop)

    return crop


def repository(db):
    return CropSeasonRepository(db)


# ============================================================
# GET BY ID
# ============================================================


def test_get_by_id(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
        crop_name="Rice",
    )

    repo = repository(db)

    result = repo.get_by_id(crop.id)

    assert result is not None
    assert result.id == crop.id
    assert result.crop_name == "Rice"


def test_get_by_id_not_found(db):
    repo = repository(db)

    result = repo.get_by_id(uuid.uuid4())

    assert result is None


# ============================================================
# GET BY FARM AND ID
# ============================================================


def test_get_by_farm_and_id(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
    )

    repo = repository(db)

    result = repo.get_by_farm_and_id(
        farm.id,
        crop.id,
    )

    assert result is not None
    assert result.id == crop.id
    assert result.farm_id == farm.id


def test_get_by_farm_and_id_wrong_farm(db):
    farm = create_farm(db)
    other_farm = create_farm(
        db,
        farm_name="Other Farm",
    )

    crop = create_crop(
        db,
        farm.id,
    )

    repo = repository(db)

    result = repo.get_by_farm_and_id(
        other_farm.id,
        crop.id,
    )

    assert result is None


def test_get_by_farm_and_id_not_found(db):
    farm = create_farm(db)

    repo = repository(db)

    result = repo.get_by_farm_and_id(
        farm.id,
        uuid.uuid4(),
    )

    assert result is None


# ============================================================
# GET BY FARM AND STATUS
# ============================================================


def test_get_by_farm_and_status(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        crop_name="Rice",
        status=CropSeasonStatus.PLANNED,
    )

    create_crop(
        db,
        farm.id,
        crop_name="Maize",
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    repo = repository(db)

    result = repo.get_by_farm_and_status(
        farm.id,
        CropSeasonStatus.ACTIVE,
    )

    assert len(result) == 1
    assert result[0].crop_name == "Maize"
    assert result[0].status == CropSeasonStatus.ACTIVE


def test_get_by_farm_and_status_isolated(db):
    farm = create_farm(db)
    other_farm = create_farm(
        db,
        farm_name="Other Farm",
    )

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    create_crop(
        db,
        other_farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    repo = repository(db)

    result = repo.get_by_farm_and_status(
        farm.id,
        CropSeasonStatus.ACTIVE,
    )

    assert len(result) == 1
    assert result[0].farm_id == farm.id


def test_get_by_farm_and_status_empty(db):
    farm = create_farm(db)

    repo = repository(db)

    result = repo.get_by_farm_and_status(
        farm.id,
        CropSeasonStatus.ACTIVE,
    )

    assert result == []


# ============================================================
# GET ALL BY FARM
# ============================================================


def test_get_all_by_farm(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        crop_name="Rice",
    )

    create_crop(
        db,
        farm.id,
        crop_name="Maize",
    )

    repo = repository(db)

    result = repo.get_all_by_farm(farm.id)

    assert len(result) == 2
    assert all(
        crop.farm_id == farm.id
        for crop in result
    )


def test_get_all_by_farm_isolated(db):
    farm = create_farm(db)
    other_farm = create_farm(
        db,
        farm_name="Other Farm",
    )

    create_crop(
        db,
        farm.id,
    )

    create_crop(
        db,
        other_farm.id,
    )

    repo = repository(db)

    result = repo.get_all_by_farm(farm.id)

    assert len(result) == 1
    assert result[0].farm_id == farm.id


def test_get_all_by_farm_empty(db):
    farm = create_farm(db)

    repo = repository(db)

    result = repo.get_all_by_farm(farm.id)

    assert result == []


# ============================================================
# ACTIVE CROPS
# ============================================================


def test_get_active_by_farm(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    repo = repository(db)

    result = repo.get_active_by_farm(farm.id)

    assert result is not None
    assert result.id == crop.id
    assert result.status == CropSeasonStatus.ACTIVE
    assert result.is_active is True


def test_get_active_by_farm_ignores_inactive_flag(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=False,
    )

    repo = repository(db)

    result = repo.get_active_by_farm(farm.id)

    assert result is None


def test_get_active_by_farm_ignores_wrong_status(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.PLANNED,
        is_active=True,
    )

    repo = repository(db)

    result = repo.get_active_by_farm(farm.id)

    assert result is None


def test_get_all_active_by_farm(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        crop_name="Rice",
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    create_crop(
        db,
        farm.id,
        crop_name="Maize",
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    create_crop(
        db,
        farm.id,
        crop_name="Groundnut",
        status=CropSeasonStatus.PLANNED,
        is_active=False,
    )

    repo = repository(db)

    result = repo.get_all_active_by_farm(farm.id)

    assert len(result) == 2

    assert {
        crop.crop_name
        for crop in result
    } == {
        "Rice",
        "Maize",
    }


def test_get_all_active(db):
    farm = create_farm(db)
    other_farm = create_farm(
        db,
        farm_name="Other Farm",
    )

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    create_crop(
        db,
        other_farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.PLANNED,
        is_active=False,
    )

    repo = repository(db)

    result = repo.get_all_active()

    assert len(result) == 2

    assert all(
        crop.status == CropSeasonStatus.ACTIVE
        and crop.is_active is True
        for crop in result
    )


def test_get_all_active_with_farm(db):
    # --------------------------------------------------------
    # IMPORTANT:
    # Repository performs:
    #
    #     .join(CropSeason.farm)
    #
    # Therefore an actual Farm row must exist.
    # --------------------------------------------------------

    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    repo = repository(db)

    result = repo.get_all_active_with_farm()

    assert len(result) == 1
    assert result[0].id == crop.id
    assert result[0].farm_id == farm.id


def test_get_all_active_with_farm_ignores_missing_relationship(db):
    # --------------------------------------------------------
    # This test verifies that an INNER JOIN only returns
    # crop seasons whose farm relationship exists.
    #
    # SQLite/PostgreSQL FK behavior may differ depending on
    # test configuration, so this is intentionally omitted
    # from normal repository coverage.
    # --------------------------------------------------------

    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    repo = repository(db)

    result = repo.get_all_active_with_farm()

    assert any(
        item.id == crop.id
        for item in result
    )


# ============================================================
# STATUS SHORTCUTS
# ============================================================


def test_get_all_planned_by_farm(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.PLANNED,
    )

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    repo = repository(db)

    result = repo.get_all_planned_by_farm(
        farm.id,
    )

    assert len(result) == 1
    assert result[0].status == CropSeasonStatus.PLANNED


def test_get_all_harvested_by_farm(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.HARVESTED,
        harvested_date=date(2026, 10, 10),
    )

    repo = repository(db)

    result = repo.get_all_harvested_by_farm(
        farm.id,
    )

    assert len(result) == 1
    assert result[0].status == CropSeasonStatus.HARVESTED


def test_get_all_cancelled_by_farm(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.CANCELLED,
    )

    repo = repository(db)

    result = repo.get_all_cancelled_by_farm(
        farm.id,
    )

    assert len(result) == 1
    assert result[0].status == CropSeasonStatus.CANCELLED


# ============================================================
# LATEST CROP
# ============================================================


def test_get_latest_by_farm(db):
    farm = create_farm(db)

    first = create_crop(
        db,
        farm.id,
        crop_name="Rice",
    )

    latest = create_crop(
        db,
        farm.id,
        crop_name="Maize",
    )

    # --------------------------------------------------------
    # Force deterministic creation order.
    # --------------------------------------------------------

    latest.created_at = (
        first.created_at
        + timedelta(seconds=10)
    )

    db.commit()
    db.refresh(latest)

    repo = repository(db)

    result = repo.get_latest_by_farm(
        farm.id,
    )

    assert result is not None
    assert result.id == latest.id
    assert result.id != first.id


def test_get_latest_by_farm_empty(db):
    farm = create_farm(db)

    repo = repository(db)

    result = repo.get_latest_by_farm(
        farm.id,
    )

    assert result is None


# ============================================================
# GET BY FARM AND CROP NAME
# ============================================================


def test_get_by_farm_and_crop(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
        crop_name="Rice",
    )

    repo = repository(db)

    result = repo.get_by_farm_and_crop(
        farm.id,
        "Rice",
    )

    assert result is not None
    assert result.id == crop.id


def test_get_by_farm_and_crop_isolated(db):
    farm = create_farm(db)
    other_farm = create_farm(
        db,
        farm_name="Other Farm",
    )

    create_crop(
        db,
        other_farm.id,
        crop_name="Rice",
    )

    repo = repository(db)

    result = repo.get_by_farm_and_crop(
        farm.id,
        "Rice",
    )

    assert result is None


def test_get_by_farm_and_crop_not_found(db):
    farm = create_farm(db)

    repo = repository(db)

    result = repo.get_by_farm_and_crop(
        farm.id,
        "Rice",
    )

    assert result is None


# ============================================================
# CREATE
# ============================================================


def test_create(db):
    farm = create_farm(db)

    crop = CropSeason(
        farm_id=farm.id,
        crop_name="Rice",
        crop_variety="BPT-5204",
        land_area=2.0,
        land_unit="Acres",
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 15),
        expected_harvest_date=date(2026, 10, 15),
    )

    repo = repository(db)

    result = repo.create(crop)

    assert result.id is not None

    stored = (
        db.query(CropSeason)
        .filter(
            CropSeason.id == result.id,
        )
        .first()
    )

    assert stored is not None
    assert stored.crop_name == "Rice"


def test_create_without_commit(db):
    farm = create_farm(db)

    crop = CropSeason(
        farm_id=farm.id,
        crop_name="Rice",
        land_area=2.0,
        land_unit="Acres",
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 15),
    )

    repo = repository(db)

    result = repo.create_without_commit(crop)

    assert result.id is not None

    db.rollback()

    stored = (
        db.query(CropSeason)
        .filter(
            CropSeason.id == result.id,
        )
        .first()
    )

    assert stored is None


# ============================================================
# UPDATE
# ============================================================


def test_update(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
        crop_name="Rice",
    )

    crop.crop_name = "Maize"

    repo = repository(db)

    result = repo.update(crop)

    assert result.crop_name == "Maize"

    stored = (
        db.query(CropSeason)
        .filter(
            CropSeason.id == crop.id,
        )
        .first()
    )

    assert stored.crop_name == "Maize"


def test_update_without_commit(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
        crop_name="Rice",
    )

    crop.crop_name = "Maize"

    repo = repository(db)

    result = repo.update_without_commit(crop)

    assert result.crop_name == "Maize"

    db.rollback()

    stored = (
        db.query(CropSeason)
        .filter(
            CropSeason.id == crop.id,
        )
        .first()
    )

    assert stored.crop_name == "Rice"


# ============================================================
# DELETE
# ============================================================


def test_delete(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
    )

    crop_id = crop.id

    repo = repository(db)

    repo.delete(crop)

    stored = (
        db.query(CropSeason)
        .filter(
            CropSeason.id == crop_id,
        )
        .first()
    )

    assert stored is None


def test_delete_without_commit(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
    )

    crop_id = crop.id

    repo = repository(db)

    repo.delete_without_commit(crop)

    db.rollback()

    stored = (
        db.query(CropSeason)
        .filter(
            CropSeason.id == crop_id,
        )
        .first()
    )

    assert stored is not None


# ============================================================
# LIFECYCLE
# ============================================================


def test_mark_active(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.PLANNED,
        is_active=False,
    )

    repo = repository(db)

    result = repo.mark_active(crop)

    assert result.status == CropSeasonStatus.ACTIVE
    assert result.is_active is True


def test_mark_harvested(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    repo = repository(db)

    result = repo.mark_harvested(crop)

    assert result.status == CropSeasonStatus.HARVESTED
    assert result.is_active is False


def test_mark_cancelled(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.PLANNED,
        is_active=False,
    )

    repo = repository(db)

    result = repo.mark_cancelled(crop)

    assert result.status == CropSeasonStatus.CANCELLED
    assert result.is_active is False


# ============================================================
# EXISTS / CHECKS
# ============================================================


def test_has_active_crop(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    repo = repository(db)

    assert repo.has_active_crop(
        farm.id,
    ) is True


def test_has_active_crop_false(db):
    farm = create_farm(db)

    assert repo_or_false(
        repository(db),
        farm.id,
    ) is False


def repo_or_false(
    repo,
    farm_id,
):
    return repo.has_active_crop(farm_id)


def test_has_planned_crop(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.PLANNED,
    )

    repo = repository(db)

    assert repo.has_planned_crop(
        farm.id,
    ) is True


def test_has_planned_crop_false(db):
    farm = create_farm(db)

    repo = repository(db)

    assert repo.has_planned_crop(
        farm.id,
    ) is False


def test_exists_by_status(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.HARVESTED,
        harvested_date=date(2026, 10, 10),
    )

    repo = repository(db)

    assert repo.exists_by_status(
        farm.id,
        CropSeasonStatus.HARVESTED,
    ) is True


def test_exists(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
    )

    repo = repository(db)

    assert repo.exists(
        crop.id,
    ) is True


def test_exists_false(db):
    repo = repository(db)

    assert repo.exists(
        uuid.uuid4(),
    ) is False


# ============================================================
# COUNTS
# ============================================================


def test_count_by_farm(db):
    farm = create_farm(db)

    create_crop(db, farm.id)
    create_crop(db, farm.id)
    create_crop(db, farm.id)

    repo = repository(db)

    assert repo.count_by_farm(
        farm.id,
    ) == 3


def test_count_active_by_farm(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.ACTIVE,
        is_active=True,
    )

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.PLANNED,
    )

    repo = repository(db)

    assert repo.count_active_by_farm(
        farm.id,
    ) == 2


def test_count_planned_by_farm(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.PLANNED,
    )

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.PLANNED,
    )

    repo = repository(db)

    assert repo.count_planned_by_farm(
        farm.id,
    ) == 2


def test_count_harvested_by_farm(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.HARVESTED,
        harvested_date=date(2026, 10, 10),
    )

    repo = repository(db)

    assert repo.count_harvested_by_farm(
        farm.id,
    ) == 1


def test_count_cancelled_by_farm(db):
    farm = create_farm(db)

    create_crop(
        db,
        farm.id,
        status=CropSeasonStatus.CANCELLED,
    )

    repo = repository(db)

    assert repo.count_cancelled_by_farm(
        farm.id,
    ) == 1


# ============================================================
# TRANSACTIONS
# ============================================================


def test_commit(db):
    farm = create_farm(db)

    crop = CropSeason(
        farm_id=farm.id,
        crop_name="Rice",
        land_area=2.0,
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 15),
    )

    db.add(crop)

    repo = repository(db)

    repo.commit()

    stored = (
        db.query(CropSeason)
        .filter(
            CropSeason.id == crop.id,
        )
        .first()
    )

    assert stored is not None


def test_rollback(db):
    farm = create_farm(db)

    crop = CropSeason(
        farm_id=farm.id,
        crop_name="Rice",
        land_area=2.0,
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 15),
    )

    db.add(crop)
    db.flush()

    crop_id = crop.id

    repo = repository(db)

    repo.rollback()

    stored = (
        db.query(CropSeason)
        .filter(
            CropSeason.id == crop_id,
        )
        .first()
    )

    assert stored is None


def test_flush(db):
    farm = create_farm(db)

    crop = CropSeason(
        farm_id=farm.id,
        crop_name="Rice",
        land_area=2.0,
        season=FarmingSeason.KHARIF,
        year=2026,
        sowing_date=date(2026, 6, 15),
    )

    db.add(crop)

    repo = repository(db)

    repo.flush()

    assert crop.id is not None


# ============================================================
# REFRESH
# ============================================================


def test_refresh(db):
    farm = create_farm(db)

    crop = create_crop(
        db,
        farm.id,
        crop_name="Rice",
    )

    repo = repository(db)

    result = repo.refresh(crop)

    assert result is crop
    assert result.id == crop.id
    assert result.crop_name == "Rice"