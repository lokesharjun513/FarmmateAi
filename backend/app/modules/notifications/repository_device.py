from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.notifications.models_device import DeviceToken


class DeviceTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_fid(self, fid: str) -> DeviceToken | None:
        return (
            self.db.query(DeviceToken)
            .filter(DeviceToken.fid == fid)
            .first()
        )

    def get_by_farmer(self, farmer_id: UUID) -> list[DeviceToken]:
        return (
            self.db.query(DeviceToken)
            .filter(DeviceToken.farmer_id == farmer_id)
            .all()
        )

    def create(self, device_token: DeviceToken) -> DeviceToken:
        try:
            self.db.add(device_token)
            self.db.commit()
            self.db.refresh(device_token)
            return device_token
        except IntegrityError:
            self.db.rollback()
            raise

    def update(self, device_token: DeviceToken) -> DeviceToken:
        try:
            self.db.commit()
            self.db.refresh(device_token)
            return device_token
        except IntegrityError:
            self.db.rollback()
            raise

    def delete(self, device_token: DeviceToken) -> None:
        self.db.delete(device_token)
        self.db.commit()

    def delete_by_fid(self, fid: str) -> None:
        self.db.query(DeviceToken).filter(
            DeviceToken.fid == fid
        ).delete()
        self.db.commit()

    def delete_by_fid_for_farmer(
        self,
        fid: str,
        farmer_id: UUID,
    ) -> bool:
        deleted = (
            self.db.query(DeviceToken)
            .filter(
                DeviceToken.fid == fid,
                DeviceToken.farmer_id == farmer_id,
            )
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted > 0

    def delete_by_fids(self, fids: Sequence[str]) -> None:
        if not fids:
            return

        self.db.query(DeviceToken).filter(
            DeviceToken.fid.in_(list(fids))
        ).delete(synchronize_session=False)
        self.db.commit()
