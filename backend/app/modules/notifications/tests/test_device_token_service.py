from uuid import uuid4

from app.modules.notifications.repository_device import (
    DeviceTokenRepository,
)
from app.modules.notifications.service_device import (
    deactivate_device_token,
    register_device_token,
)


def test_register_device_fid_creates_registration(db):

    farmer_id = uuid4()

    registration = register_device_token(
        db=db,
        farmer_id=farmer_id,
        fid=" fid-1 ",
        device_name="Android",
    )

    assert registration.fid == "fid-1"
    assert registration.farmer_id == farmer_id
    assert registration.device_name == "Android"


def test_register_device_fid_is_idempotent(db):

    farmer_id = uuid4()

    first = register_device_token(
        db=db,
        farmer_id=farmer_id,
        fid="fid-1",
        device_name="Android",
    )
    second = register_device_token(
        db=db,
        farmer_id=farmer_id,
        fid="fid-1",
        device_name="Pixel",
    )

    repository = DeviceTokenRepository(db)

    assert first.id == second.id
    assert second.device_name == "Pixel"
    assert len(repository.get_by_farmer(farmer_id)) == 1


def test_register_device_fid_transfers_ownership(db):

    first_farmer = uuid4()
    second_farmer = uuid4()

    register_device_token(
        db=db,
        farmer_id=first_farmer,
        fid="shared-fid",
    )
    registration = register_device_token(
        db=db,
        farmer_id=second_farmer,
        fid="shared-fid",
    )

    repository = DeviceTokenRepository(db)

    assert registration.farmer_id == second_farmer
    assert repository.get_by_farmer(first_farmer) == []
    assert len(repository.get_by_farmer(second_farmer)) == 1


def test_deactivate_device_fid_only_removes_owner_fid(db):

    owner_id = uuid4()
    other_farmer_id = uuid4()

    register_device_token(
        db=db,
        farmer_id=owner_id,
        fid="owner-fid",
    )

    removed = deactivate_device_token(
        db=db,
        farmer_id=other_farmer_id,
        fid="owner-fid",
    )

    repository = DeviceTokenRepository(db)

    assert removed is False
    assert repository.get_by_fid("owner-fid") is not None


def test_deactivate_device_fid_is_idempotent(db):

    farmer_id = uuid4()

    register_device_token(
        db=db,
        farmer_id=farmer_id,
        fid="fid-1",
    )

    assert (
        deactivate_device_token(
            db=db,
            farmer_id=farmer_id,
            fid="fid-1",
        )
        is True
    )
    assert (
        deactivate_device_token(
            db=db,
            farmer_id=farmer_id,
            fid="fid-1",
        )
        is False
    )
