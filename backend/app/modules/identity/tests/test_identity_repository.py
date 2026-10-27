from uuid import uuid4

from app.modules.identity.models import User
from app.modules.identity.repository import UserRepository


# ============================================================
# HELPERS
# ============================================================


def create_user(
    db,
    *,
    full_name="Test Farmer",
    mobile=None,
    email=None,
    is_active=True,
):

    user = User(
        id=uuid4(),
        full_name=full_name,
        mobile=mobile or f"{uuid4().hex[:10]}",
        email=email or f"{uuid4().hex[:10]}@test.com",
        password_hash="hashed-password",
        is_active=is_active,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# GET BY ID
# ============================================================


def test_get_by_id(db):

    user = create_user(db)

    repository = UserRepository(db)

    result = repository.get_by_id(
        user.id,
    )

    assert result is not None
    assert result.id == user.id


def test_get_by_id_not_found(db):

    repository = UserRepository(db)

    result = repository.get_by_id(
        uuid4(),
    )

    assert result is None


# ============================================================
# GET BY EMAIL
# ============================================================


def test_get_by_email(db):

    user = create_user(
        db,
        email="test@example.com",
    )

    repository = UserRepository(db)

    result = repository.get_by_email(
        "test@example.com",
    )

    assert result is not None
    assert result.id == user.id


def test_get_by_email_normalizes_email(db):

    user = create_user(
        db,
        email="test@example.com",
    )

    repository = UserRepository(db)

    result = repository.get_by_email(
        "  TEST@EXAMPLE.COM ",
    )

    assert result is not None
    assert result.id == user.id


def test_get_by_email_not_found(db):

    repository = UserRepository(db)

    result = repository.get_by_email(
        "missing@example.com",
    )

    assert result is None


# ============================================================
# GET BY MOBILE
# ============================================================


def test_get_by_mobile(db):

    user = create_user(
        db,
        mobile="9876543210",
    )

    repository = UserRepository(db)

    result = repository.get_by_mobile(
        "9876543210",
    )

    assert result is not None
    assert result.id == user.id


def test_get_by_mobile_trims_value(db):

    user = create_user(
        db,
        mobile="9876543210",
    )

    repository = UserRepository(db)

    result = repository.get_by_mobile(
        " 9876543210 ",
    )

    assert result is not None
    assert result.id == user.id


def test_get_by_mobile_not_found(db):

    repository = UserRepository(db)

    result = repository.get_by_mobile(
        "9999999999",
    )

    assert result is None


# ============================================================
# GET BY IDENTIFIER
# ============================================================


def test_get_by_identifier_email(db):

    user = create_user(
        db,
        email="test@example.com",
    )

    repository = UserRepository(db)

    result = repository.get_by_identifier(
        "TEST@EXAMPLE.COM",
    )

    assert result is not None
    assert result.id == user.id


def test_get_by_identifier_mobile(db):

    user = create_user(
        db,
        mobile="9876543210",
    )

    repository = UserRepository(db)

    result = repository.get_by_identifier(
        "9876543210",
    )

    assert result is not None
    assert result.id == user.id


def test_get_by_identifier_not_found(db):

    repository = UserRepository(db)

    result = repository.get_by_identifier(
        "missing@example.com",
    )

    assert result is None


# ============================================================
# CREATE
# ============================================================


def test_create_user(db):

    repository = UserRepository(db)

    user = User(
        id=uuid4(),
        full_name="Created User",
        mobile="9876543210",
        email="created@example.com",
        password_hash="hashed-password",
        is_active=True,
    )

    result = repository.create(user)

    assert result.id == user.id
    assert result.full_name == "Created User"

    stored = repository.get_by_id(
        user.id,
    )

    assert stored is not None
    assert stored.email == "created@example.com"