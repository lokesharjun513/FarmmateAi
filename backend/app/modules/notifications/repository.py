from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification


class NotificationRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ========================================================
    # GET NOTIFICATION BY ID
    # ========================================================

    def get_by_id(
        self,
        notification_id: UUID,
    ) -> Notification | None:

        return (
            self.db.query(Notification)
            .filter(
                Notification.id == notification_id,
            )
            .first()
        )

    # ========================================================
    # GET ALL NOTIFICATIONS FOR FARMER
    #
    # Newest notifications first.
    # ========================================================

    def get_all_by_farmer(
        self,
        farmer_id: UUID,
    ) -> list[Notification]:

        return (
            self.db.query(Notification)
            .filter(
                Notification.farmer_id == farmer_id,
            )
            .order_by(
                Notification.created_at.desc(),
            )
            .all()
        )

    # ========================================================
    # GET UNREAD NOTIFICATIONS
    #
    # Newest unread notifications first.
    # ========================================================

    def get_unread_by_farmer(
        self,
        farmer_id: UUID,
    ) -> list[Notification]:

        return (
            self.db.query(Notification)
            .filter(
                Notification.farmer_id == farmer_id,
                Notification.is_read.is_(False),
            )
            .order_by(
                Notification.created_at.desc(),
            )
            .all()
        )

    # ========================================================
    # COUNT UNREAD NOTIFICATIONS
    #
    # Used for:
    #
    # - Notification badge
    # - Dashboard
    # - Mobile header
    # ========================================================

    def count_unread_by_farmer(
        self,
        farmer_id: UUID,
    ) -> int:

        return (
            self.db.query(Notification)
            .filter(
                Notification.farmer_id == farmer_id,
                Notification.is_read.is_(False),
            )
            .count()
        )

    # ========================================================
    # CREATE NOTIFICATION
    # ========================================================

    def create(
        self,
        notification: Notification,
    ) -> Notification:

        try:

            self.db.add(notification)

            self.db.commit()

            self.db.refresh(notification)

            return notification

        except Exception:

            self.db.rollback()

            raise

    # ========================================================
    # UPDATE NOTIFICATION
    # ========================================================

    def update(
        self,
        notification: Notification,
    ) -> Notification:

        try:

            self.db.commit()

            self.db.refresh(notification)

            return notification

        except Exception:

            self.db.rollback()

            raise

    # ========================================================
    # MARK ALL NOTIFICATIONS AS READ
    #
    # Returns the number of notifications updated.
    #
    # Example:
    #
    # 5 unread notifications
    #       ↓
    # mark_all_read()
    #       ↓
    # returns 5
    #
    # Idempotent:
    #
    # First call  → 5
    # Second call → 0
    # ========================================================

    def mark_all_read(
        self,
        farmer_id: UUID,
    ) -> int:

        try:

            updated_count = (
                self.db.query(Notification)
                .filter(
                    Notification.farmer_id == farmer_id,
                    Notification.is_read.is_(False),
                )
                .update(
                    {
                        Notification.is_read: True,
                    },
                    synchronize_session=False,
                )
            )

            self.db.commit()

            return updated_count

        except Exception:

            self.db.rollback()

            raise

    # ========================================================
    # DELETE NOTIFICATION
    # ========================================================

    def delete(
        self,
        notification: Notification,
    ) -> None:

        try:

            self.db.delete(notification)

            self.db.commit()

        except Exception:

            self.db.rollback()

            raise