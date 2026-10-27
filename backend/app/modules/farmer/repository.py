from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.farmer.models import Farmer


class FarmerRepository:

    def __init__(self, db: Session):
        self.db = db

    # ========================================================
    # GET BY USER ID
    # ========================================================

    def get_by_user_id(
        self,
        user_id: UUID,
    ) -> Farmer | None:

        statement = (
            select(Farmer)
            .where(Farmer.user_id == user_id)
        )

        return self.db.scalar(statement)

    # ========================================================
    # GET BY FARMER ID
    # ========================================================

    def get_by_id(
        self,
        farmer_id: UUID,
    ) -> Farmer | None:

        statement = (
            select(Farmer)
            .where(Farmer.id == farmer_id)
        )

        return self.db.scalar(statement)

    # ========================================================
    # CREATE
    # ========================================================

    def create(
        self,
        farmer: Farmer,
    ) -> Farmer:

        try:

            self.db.add(farmer)

            self.db.commit()

            self.db.refresh(farmer)

            return farmer

        except IntegrityError:

            self.db.rollback()

            raise

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        farmer: Farmer,
    ) -> Farmer:

        try:

            self.db.commit()

            self.db.refresh(farmer)

            return farmer

        except IntegrityError:

            self.db.rollback()

            raise