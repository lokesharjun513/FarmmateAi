from types import SimpleNamespace

from firebase_admin import messaging

from app.modules.notifications import fcm_service


def test_missing_firebase_configuration_is_non_fatal(monkeypatch):

    monkeypatch.setattr(
        fcm_service.settings,
        "FIREBASE_SERVICE_ACCOUNT_KEY_PATH",
        None,
    )
    monkeypatch.delenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        raising=False,
    )
    monkeypatch.setattr(fcm_service, "_FIREBASE_READY", None)

    result = fcm_service.send_push_notification(
        fids=["token-1"],
        title="Weather",
        message="Rain expected.",
    )

    assert result == []


def test_delivery_returns_invalid_fids(monkeypatch):

    monkeypatch.setattr(
        fcm_service,
        "_initialize_firebase",
        lambda: True,
    )

    response = SimpleNamespace(
        responses=[
            SimpleNamespace(success=True, exception=None),
            SimpleNamespace(
                success=False,
                exception=messaging.UnregisteredError("unregistered"),
            ),
            SimpleNamespace(
                success=False,
                exception=RuntimeError("temporary failure"),
            ),
        ]
    )

    monkeypatch.setattr(
        fcm_service.messaging,
        "send_each_for_multicast",
        lambda payload: response,
    )

    stale = fcm_service.send_push_notification(
        fids=["valid", "stale", "temporary"],
        title="Weather",
        message="Rain expected.",
    )

    assert stale == ["stale"]


def test_batch_delivery_failure_is_swallowed(monkeypatch):

    monkeypatch.setattr(
        fcm_service,
        "_initialize_firebase",
        lambda: True,
    )

    def fail(payload):
        raise RuntimeError("FCM unavailable")

    monkeypatch.setattr(
        fcm_service.messaging,
        "send_each_for_multicast",
        fail,
    )

    stale = fcm_service.send_push_notification(
        fids=["token-1"],
        title="Weather",
        message="Rain expected.",
    )

    assert stale == []
