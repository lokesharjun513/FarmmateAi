from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.identity.models import User


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    # ========================================================
    # GET BY ID
    # ========================================================

    def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:

        statement = (
            select(User)
            .where(User.id == user_id)
        )

        return self.db.scalar(statement)

    # ========================================================
    # GET BY EMAIL
    # ========================================================

    def get_by_email(
        self,
        email: str,
    ) -> User | None:

        normalized_email = email.strip().lower()

        statement = (
            select(User)
            .where(User.email == normalized_email)
        )

        return self.db.scalar(statement)

    # ========================================================
    # GET BY MOBILE
    # ========================================================

    def get_by_mobile(
        self,
        mobile: str,
    ) -> User | None:

        normalized_mobile = mobile.strip()

        statement = (
            select(User)
            .where(User.mobile == normalized_mobile)
        )

        return self.db.scalar(statement)

    # ========================================================
    # GET BY EMAIL OR MOBILE
    # ========================================================

    def get_by_identifier(
        self,
        identifier: str,
    ) -> User | None:

        normalized_identifier = identifier.strip().lower()

        statement = (
            select(User)
            .where(
                or_(
                    User.email == normalized_identifier,
                    User.mobile == normalized_identifier,
                )
            )
        )

        return self.db.scalar(statement)

    # ========================================================
    # CREATE USER
    # ========================================================

    def create(
        self,
        user: User,
    ) -> User:

        try:

            self.db.add(user)

            self.db.commit()

            self.db.refresh(user)

            return user

        except IntegrityError:

            self.db.rollback()

            raise