from enum import Enum


# ============================================================
# FARMING SEASON
# ============================================================


class FarmingSeason(str, Enum):
    """
    Major farming seasons used by FarmMate AI.
    """

    KHARIF = "KHARIF"
    RABI = "RABI"
    ZAID = "ZAID"


# ============================================================
# SEASON MONTHS
# ============================================================

# June -> October
KHARIF_MONTHS = (
    6,
    7,
    8,
    9,
    10,
)


# November -> March
RABI_MONTHS = (
    11,
    12,
    1,
    2,
    3,
)


# April -> May
ZAID_MONTHS = (
    4,
    5,
)


# ============================================================
# GET CURRENT FARMING SEASON
# ============================================================


def get_current_farming_season(
    month: int,
) -> FarmingSeason:
    """
    Return the farming season for a calendar month.

    Month mapping:

        1  -> RABI
        2  -> RABI
        3  -> RABI

        4  -> ZAID
        5  -> ZAID

        6  -> KHARIF
        7  -> KHARIF
        8  -> KHARIF
        9  -> KHARIF
        10 -> KHARIF

        11 -> RABI
        12 -> RABI

    Raises:
        TypeError:
            If month is not an integer.

        ValueError:
            If month is outside the range 1-12.
    """

    # --------------------------------------------------------
    # Type validation
    # --------------------------------------------------------

    if isinstance(month, bool) or not isinstance(
        month,
        int,
    ):

        raise TypeError(
            "Month must be an integer."
        )

    # --------------------------------------------------------
    # Range validation
    # --------------------------------------------------------

    if not 1 <= month <= 12:

        raise ValueError(
            "Month must be between 1 and 12."
        )

    # --------------------------------------------------------
    # Kharif
    # --------------------------------------------------------

    if month in KHARIF_MONTHS:

        return FarmingSeason.KHARIF

    # --------------------------------------------------------
    # Rabi
    # --------------------------------------------------------

    if month in RABI_MONTHS:

        return FarmingSeason.RABI

    # --------------------------------------------------------
    # Zaid
    # --------------------------------------------------------

    return FarmingSeason.ZAID