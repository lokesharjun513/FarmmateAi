import pytest

from app.modules.master.seasons import (
    FarmingSeason,
    KHARIF_MONTHS,
    RABI_MONTHS,
    ZAID_MONTHS,
    get_current_farming_season,
)


# ============================================================
# FARMING SEASON ENUM
# ============================================================


def test_farming_season_values():

    assert FarmingSeason.KHARIF.value == "KHARIF"

    assert FarmingSeason.RABI.value == "RABI"

    assert FarmingSeason.ZAID.value == "ZAID"


def test_farming_season_contains_exactly_three_values():

    assert list(FarmingSeason) == [
        FarmingSeason.KHARIF,
        FarmingSeason.RABI,
        FarmingSeason.ZAID,
    ]


def test_farming_season_is_string_enum():

    assert isinstance(
        FarmingSeason.KHARIF,
        str,
    )

    assert isinstance(
        FarmingSeason.RABI,
        str,
    )

    assert isinstance(
        FarmingSeason.ZAID,
        str,
    )


# ============================================================
# KHARIF MONTHS
# ============================================================


def test_kharif_months():

    assert KHARIF_MONTHS == (
        6,
        7,
        8,
        9,
        10,
    )


def test_kharif_has_five_months():

    assert len(KHARIF_MONTHS) == 5


@pytest.mark.parametrize(
    "month",
    [
        6,
        7,
        8,
        9,
        10,
    ],
)
def test_kharif_month_returns_kharif(
    month,
):

    result = get_current_farming_season(
        month,
    )

    assert result == FarmingSeason.KHARIF


# ============================================================
# RABI MONTHS
# ============================================================


def test_rabi_months():

    assert RABI_MONTHS == (
        11,
        12,
        1,
        2,
        3,
    )


def test_rabi_has_five_months():

    assert len(RABI_MONTHS) == 5


@pytest.mark.parametrize(
    "month",
    [
        11,
        12,
        1,
        2,
        3,
    ],
)
def test_rabi_month_returns_rabi(
    month,
):

    result = get_current_farming_season(
        month,
    )

    assert result == FarmingSeason.RABI


# ============================================================
# ZAID MONTHS
# ============================================================


def test_zaid_months():

    assert ZAID_MONTHS == (
        4,
        5,
    )


def test_zaid_has_two_months():

    assert len(ZAID_MONTHS) == 2


@pytest.mark.parametrize(
    "month",
    [
        4,
        5,
    ],
)
def test_zaid_month_returns_zaid(
    month,
):

    result = get_current_farming_season(
        month,
    )

    assert result == FarmingSeason.ZAID


# ============================================================
# EVERY CALENDAR MONTH
# ============================================================


@pytest.mark.parametrize(
    "month, expected",
    [
        # RABI
        (1, FarmingSeason.RABI),
        (2, FarmingSeason.RABI),
        (3, FarmingSeason.RABI),

        # ZAID
        (4, FarmingSeason.ZAID),
        (5, FarmingSeason.ZAID),

        # KHARIF
        (6, FarmingSeason.KHARIF),
        (7, FarmingSeason.KHARIF),
        (8, FarmingSeason.KHARIF),
        (9, FarmingSeason.KHARIF),
        (10, FarmingSeason.KHARIF),

        # RABI
        (11, FarmingSeason.RABI),
        (12, FarmingSeason.RABI),
    ],
)
def test_every_month_has_expected_farming_season(
    month,
    expected,
):

    result = get_current_farming_season(
        month,
    )

    assert result == expected


# ============================================================
# ALL MONTHS ARE COVERED
# ============================================================


def test_all_calendar_months_are_covered():

    all_months = (
        set(KHARIF_MONTHS)
        | set(RABI_MONTHS)
        | set(ZAID_MONTHS)
    )

    assert all_months == set(
        range(1, 13),
    )


# ============================================================
# SEASON MONTHS DO NOT OVERLAP
# ============================================================


def test_kharif_and_rabi_do_not_overlap():

    assert set(KHARIF_MONTHS).isdisjoint(
        RABI_MONTHS,
    )


def test_kharif_and_zaid_do_not_overlap():

    assert set(KHARIF_MONTHS).isdisjoint(
        ZAID_MONTHS,
    )


def test_rabi_and_zaid_do_not_overlap():

    assert set(RABI_MONTHS).isdisjoint(
        ZAID_MONTHS,
    )


def test_all_season_months_are_unique():

    all_months = (
        KHARIF_MONTHS
        + RABI_MONTHS
        + ZAID_MONTHS
    )

    assert len(all_months) == len(
        set(all_months),
    )


# ============================================================
# TOTAL MONTH COUNT
# ============================================================


def test_total_month_count_is_twelve():

    total = (
        len(KHARIF_MONTHS)
        + len(RABI_MONTHS)
        + len(ZAID_MONTHS)
    )

    assert total == 12


# ============================================================
# RETURN TYPE
# ============================================================


@pytest.mark.parametrize(
    "month",
    range(1, 13),
)
def test_get_current_farming_season_returns_enum(
    month,
):

    result = get_current_farming_season(
        month,
    )

    assert isinstance(
        result,
        FarmingSeason,
    )


# ============================================================
# BOUNDARY MONTHS
# ============================================================


def test_january_is_rabi():

    assert (
        get_current_farming_season(1)
        == FarmingSeason.RABI
    )


def test_march_is_rabi():

    assert (
        get_current_farming_season(3)
        == FarmingSeason.RABI
    )


def test_april_starts_zaid():

    assert (
        get_current_farming_season(4)
        == FarmingSeason.ZAID
    )


def test_may_ends_zaid():

    assert (
        get_current_farming_season(5)
        == FarmingSeason.ZAID
    )


def test_june_starts_kharif():

    assert (
        get_current_farming_season(6)
        == FarmingSeason.KHARIF
    )


def test_october_ends_kharif():

    assert (
        get_current_farming_season(10)
        == FarmingSeason.KHARIF
    )


def test_november_starts_rabi():

    assert (
        get_current_farming_season(11)
        == FarmingSeason.RABI
    )


def test_december_is_rabi():

    assert (
        get_current_farming_season(12)
        == FarmingSeason.RABI
    )


# ============================================================
# INVALID MONTHS
# ============================================================


@pytest.mark.parametrize(
    "month",
    [
        -100,
        -12,
        -1,
        0,
        13,
        14,
        100,
    ],
)
def test_invalid_month_is_rejected(
    month,
):

    with pytest.raises(
        ValueError,
        match="Month must be between 1 and 12",
    ):

        get_current_farming_season(
            month,
        )


# ============================================================
# INVALID MONTH TYPES
# ============================================================


def test_none_month_is_rejected():

    with pytest.raises(
        TypeError,
    ):

        get_current_farming_season(
            None,
        )


def test_string_month_is_rejected():

    with pytest.raises(
        TypeError,
    ):

        get_current_farming_season(
            "6",
        )


def test_float_month_is_rejected():

    with pytest.raises(
        TypeError,
    ):

        get_current_farming_season(
            6.5,
        )


# ============================================================
# FUNCTION DETERMINISM
# ============================================================


@pytest.mark.parametrize(
    "month",
    range(1, 13),
)
def test_same_month_always_returns_same_season(
    month,
):

    first = get_current_farming_season(
        month,
    )

    second = get_current_farming_season(
        month,
    )

    assert first == second


def test_boolean_month_is_rejected():

    with pytest.raises(
        TypeError,
        match="Month must be an integer",
    ):

        get_current_farming_season(True)