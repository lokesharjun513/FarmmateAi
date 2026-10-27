from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.farm.models import Farm


class FarmRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ========================================================
    # GET FARM BY ID
    # ========================================================

    def get_by_id(
        self,
        farm_id: UUID,
    ) -> Farm | None:

        return (
            self.db.query(Farm)
            .filter(
                Farm.id == farm_id,
            )
            .first()
        )

    # ========================================================
    # GET FARM BY ID + FARMER
    #
    # Prevents one farmer from accessing another farmer's farm.
    # ========================================================

    def get_by_id_and_farmer(
        self,
        farm_id: UUID,
        farmer_id: UUID,
    ) -> Farm | None:

        return (
            self.db.query(Farm)
            .filter(
                Farm.id == farm_id,
                Farm.farmer_id == farmer_id,
            )
            .first()
        )

    # ========================================================
    # GET FARM BY ID + FARMER WITH ROW LOCK
    # ========================================================

    def get_by_id_and_farmer_for_update(
        self,
        farm_id: UUID,
        farmer_id: UUID,
    ) -> Farm | None:

        return (
            self.db.query(Farm)
            .filter(
                Farm.id == farm_id,
                Farm.farmer_id == farmer_id,
            )
            .with_for_update()
            .first()
        )

    # ========================================================
    # GET ALL FARMS FOR FARMER
    #
    # Primary farm is returned first.
    #
    # A farmer should have only one primary farm.
    #
    # If inconsistent data contains multiple primary farms,
    # the most recently created primary farm becomes the
    # effective primary farm.
    #
    # The correction is persisted to the database.
    # ========================================================

    def get_all_by_farmer(
        self,
        farmer_id: UUID,
    ) -> list[Farm]:

        farms = (
            self.db.query(Farm)
            .filter(
                Farm.farmer_id == farmer_id,
            )
            .order_by(
                Farm.created_at.asc(),
            )
            .all()
        )

        # ----------------------------------------------------
        # Find all farms currently marked as primary.
        # ----------------------------------------------------

        primary_farms = [
            farm
            for farm in farms
            if farm.is_primary
        ]

        # ----------------------------------------------------
        # If multiple farms are marked as primary,
        # keep the newest one as primary.
        # ----------------------------------------------------

        if len(primary_farms) > 1:

            primary_farm = primary_farms[-1]

            # ------------------------------------------------
            # Make all older primary farms non-primary.
            # ------------------------------------------------

            for farm in primary_farms:

                if farm.id != primary_farm.id:
                    farm.is_primary = False

            # ------------------------------------------------
            # Make sure the newest farm remains primary.
            # ------------------------------------------------

            primary_farm.is_primary = True

            # ------------------------------------------------
            # Persist the normalization.
            # ------------------------------------------------

            self.db.commit()

            # ------------------------------------------------
            # Refresh affected farms from the database.
            # ------------------------------------------------

            for farm in primary_farms:
                self.db.refresh(farm)

        # ----------------------------------------------------
        # Primary farm first.
        #
        # Remaining farms are ordered by creation time.
        # ----------------------------------------------------

        farms.sort(
            key=lambda farm: (
                not farm.is_primary,
                farm.created_at,
            ),
        )

        return farms

    # ========================================================
    # SET FARM AS PRIMARY
    #
    # Exactly one farm can be primary for a farmer.
    #
    # Before making the selected farm primary, all other farms
    # belonging to the same farmer are made non-primary.
    # ========================================================

    def set_primary(
        self,
        farm: Farm,
    ) -> None:

        (
            self.db.query(Farm.id)
            .filter(
                Farm.farmer_id == farm.farmer_id,
            )
            .order_by(
                Farm.id.asc(),
            )
            .with_for_update()
            .all()
        )

        (
            self.db.query(Farm)
            .filter(
                Farm.farmer_id == farm.farmer_id,
                Farm.id != farm.id,
            )
            .update(
                {
                    Farm.is_primary: False,
                },
                synchronize_session=False,
            )
        )

        farm.is_primary = True

    # ========================================================
    # CREATE FARM
    # ========================================================

    def create(
        self,
        farm: Farm,
    ) -> Farm:

        # ----------------------------------------------------
        # Add farm to session.
        # ----------------------------------------------------

        self.db.add(farm)

        # ----------------------------------------------------
        # Flush so the farm is attached to the transaction.
        # ----------------------------------------------------

        self.db.flush()

        # ----------------------------------------------------
        # If this farm is primary, remove primary status from
        # all other farms belonging to this farmer.
        # ----------------------------------------------------

        if farm.is_primary:

            self.set_primary(farm)

        # ----------------------------------------------------
        # Commit transaction.
        # ----------------------------------------------------

        self.db.commit()

        # ----------------------------------------------------
        # Refresh farm.
        # ----------------------------------------------------

        self.db.refresh(farm)

        return farm

    # ========================================================
    # UPDATE FARM
    # ========================================================

    def update(
        self,
        farm: Farm,
    ) -> Farm:

        # ----------------------------------------------------
        # If this farm is primary, remove primary status from
        # all other farms first.
        # ----------------------------------------------------

        if farm.is_primary:

            self.set_primary(farm)

        # ----------------------------------------------------
        # Commit changes.
        # ----------------------------------------------------

        self.db.commit()

        # ----------------------------------------------------
        # Refresh updated farm.
        # ----------------------------------------------------

        self.db.refresh(farm)

        return farm

    # ========================================================
    # DELETE FARM
    # ========================================================

    def delete(
        self,
        farm: Farm,
    ) -> None:

        self.db.delete(farm)

        self.db.commit()