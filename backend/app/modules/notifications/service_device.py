from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.notifications.models_device import DeviceToken
from app.modules.notifications.repository_device import DeviceTokenRepository


def register_device_token(
    db: Session,
    farmer_id: UUID,
    fid: str,
    device_name: str | None = None,
) -> DeviceToken:
    """
    Register or refresh a device FID for the authenticated farmer.

    FIDs are unique. If the same FID is registered by a different
    account on the same device, ownership is transferred to the
    current authenticated farmer.
    """

    repository = DeviceTokenRepository(db)
    fid = fid.strip()

    existing_token = repository.get_by_fid(fid)

    if existing_token is not None:
        return _update_registration(
            repository=repository,
            device_token=existing_token,
            farmer_id=farmer_id,
            device_name=device_name,
        )

    try:
        return repository.create(
            DeviceToken(
                farmer_id=farmer_id,
                fid=fid,
                device_name=device_name,
            )
        )
    except IntegrityError:
        # A concurrent request registered the same unique FID first.
        db.rollback()

        existing_token = repository.get_by_fid(fid)

        if existing_token is None:
            raise

        return _update_registration(
            repository=repository,
            device_token=existing_token,
            farmer_id=farmer_id,
            device_name=device_name,
        )


def _update_registration(
    repository: DeviceTokenRepository,
    device_token: DeviceToken,
    farmer_id: UUID,
    device_name: str | None,
) -> DeviceToken:
    changed = False

    if device_token.farmer_id != farmer_id:
        device_token.farmer_id = farmer_id
        changed = True

    if device_name and device_token.device_name != device_name:
        device_token.device_name = device_name
        changed = True

    if not changed:
        return device_token

    return repository.update(device_token)


def deactivate_device_token(
    db: Session,
    farmer_id: UUID,
    fid: str,
) -> bool:
    """
    Deactivate only a FID owned by the authenticated farmer.

    Returns True when a FID was removed. Repeated calls are
    idempotent and return False.
    """

    repository = DeviceTokenRepository(db)

    return repository.delete_by_fid_for_farmer(
        fid=fid.strip(),
        farmer_id=farmer_id,
    )


def unregister_device_token(
    db: Session,
    farmer_id: UUID,
    fid: str,
) -> bool:
    return deactivate_device_token(
        db=db,
        farmer_id=farmer_id,
        fid=fid,
    )
