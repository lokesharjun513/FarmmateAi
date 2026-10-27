import logging
import os
import threading
from collections.abc import Sequence

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

logger = logging.getLogger(__name__)

_FIREBASE_READY: bool | None = None
_FIREBASE_LOCK = threading.Lock()

_MAX_MULTICAST_TOKENS = 500


def _initialize_firebase() -> bool:
    """
    Initialize Firebase Admin lazily.

    The application must not fail to start when Firebase credentials
    are not configured (for example in local development or tests).
    """

    global _FIREBASE_READY

    if _FIREBASE_READY is not None:
        return _FIREBASE_READY

    with _FIREBASE_LOCK:
        if _FIREBASE_READY is not None:
            return _FIREBASE_READY

        if firebase_admin._apps:
            _FIREBASE_READY = True
            return True

        credential_path = (
            settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH
            or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        )

        if not credential_path:
            logger.warning(
                "Firebase Admin is not configured. "
                "Set FIREBASE_SERVICE_ACCOUNT_KEY_PATH or "
                "GOOGLE_APPLICATION_CREDENTIALS to enable push delivery."
            )
            _FIREBASE_READY = False
            return False

        if not os.path.isfile(credential_path):
            logger.error(
                "Firebase service account file was not found at the "
                "configured path."
            )
            _FIREBASE_READY = False
            return False

        try:
            firebase_admin.initialize_app(
                credentials.Certificate(credential_path)
            )
        except Exception:
            logger.exception("Failed to initialize Firebase Admin.")
            _FIREBASE_READY = False
            return False

        _FIREBASE_READY = True
        return True


def _is_invalid_registration(exception: Exception | None) -> bool:
    return isinstance(
        exception,
        (
            messaging.UnregisteredError,
            messaging.SenderIdMismatchError,
        ),
    )


def _chunks(values: Sequence[str], size: int) -> list[list[str]]:
    return [
        list(values[index : index + size])
        for index in range(0, len(values), size)
    ]


def send_push_notification(
    fids: Sequence[str],
    title: str,
    message: str,
    data: dict[str, str] | None = None,
) -> list[str]:
    """
    Send a notification to one or more Firebase Installation IDs.

    Returns FIDs that FCM reported as permanently invalid so the
    caller can remove them. Delivery failures are logged and never
    raised to the notification creation flow.
    """

    clean_fids = [fid.strip() for fid in fids if fid.strip()]

    if not clean_fids or not _initialize_firebase():
        return []

    stale_fids: list[str] = []

    for batch in _chunks(clean_fids, _MAX_MULTICAST_TOKENS):
        payload = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=message,
            ),
            data=data or {},
            fids=batch,
        )

        try:
            response = messaging.send_each_for_multicast(payload)
        except Exception:
            logger.exception("FCM multicast delivery failed.")
            continue

        for fid, result in zip(batch, response.responses):
            if result.success:
                continue

            if _is_invalid_registration(result.exception):
                stale_fids.append(fid)
            else:
                logger.warning(
                    "FCM delivery failed for a device registration: %s",
                    type(result.exception).__name__,
                )

    return stale_fids


def send_multicast_notification(
    fids: Sequence[str],
    title: str,
    message: str,
    data: dict[str, str] | None = None,
) -> list[str]:
    return send_push_notification(
        fids=fids,
        title=title,
        message=message,
        data=data,
    )
