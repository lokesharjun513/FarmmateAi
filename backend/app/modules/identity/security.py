import bcrypt


# ============================================================
# PASSWORD HASHING
# ============================================================


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    The plain-text password is never stored.
    """

    if not password:
        raise ValueError("Password cannot be empty.")

    password_bytes = password.encode("utf-8")

    hashed_password = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    )

    return hashed_password.decode("utf-8")


# ============================================================
# PASSWORD VERIFICATION
# ============================================================


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.

    Returns False for invalid or corrupted stored hashes
    instead of allowing the authentication request to fail.
    """

    if not password or not hashed_password:
        return False

    try:

        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )

    except (ValueError, TypeError):
        return False