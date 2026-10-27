import pytest
from pydantic import ValidationError

from app.modules.notifications.schemas import (
    NotificationCreateRequest,
    NotificationPriority,
    NotificationType,
)


# ============================================================
# VALID REQUEST
# ============================================================


def test_create_request_valid():

    request = NotificationCreateRequest(
        title="Weather Alert",
        message="Heavy rain is expected tomorrow.",
        type=NotificationType.WEATHER,
        priority=NotificationPriority.HIGH,
    )

    assert request.title == "Weather Alert"
    assert request.message == "Heavy rain is expected tomorrow."
    assert request.type == NotificationType.WEATHER
    assert request.priority == NotificationPriority.HIGH


# ============================================================
# DEFAULT PRIORITY
# ============================================================


def test_create_request_default_priority():

    request = NotificationCreateRequest(
        title="System Update",
        message="Your profile was updated.",
        type=NotificationType.SYSTEM,
    )

    assert request.priority == NotificationPriority.MEDIUM


# ============================================================
# TITLE TRIMMING
# ============================================================


def test_title_is_trimmed():

    request = NotificationCreateRequest(
        title="   Weather Alert   ",
        message="Rain expected.",
        type=NotificationType.WEATHER,
    )

    assert request.title == "Weather Alert"


# ============================================================
# MESSAGE TRIMMING
# ============================================================


def test_message_is_trimmed():

    request = NotificationCreateRequest(
        title="Weather",
        message="   Rain expected tomorrow.   ",
        type=NotificationType.WEATHER,
    )

    assert request.message == "Rain expected tomorrow."


# ============================================================
# EMPTY TITLE
# ============================================================


def test_title_cannot_be_empty():

    with pytest.raises(ValidationError):

        NotificationCreateRequest(
            title="",
            message="Valid message",
            type=NotificationType.SYSTEM,
        )


# ============================================================
# WHITESPACE TITLE
# ============================================================


def test_title_cannot_be_only_spaces():

    with pytest.raises(ValidationError):

        NotificationCreateRequest(
            title="   ",
            message="Valid message",
            type=NotificationType.SYSTEM,
        )


# ============================================================
# EMPTY MESSAGE
# ============================================================


def test_message_cannot_be_empty():

    with pytest.raises(ValidationError):

        NotificationCreateRequest(
            title="Valid title",
            message="",
            type=NotificationType.SYSTEM,
        )


# ============================================================
# WHITESPACE MESSAGE
# ============================================================


def test_message_cannot_be_only_spaces():

    with pytest.raises(ValidationError):

        NotificationCreateRequest(
            title="Valid title",
            message="   ",
            type=NotificationType.SYSTEM,
        )


# ============================================================
# SHORT TITLE
# ============================================================


def test_title_must_have_minimum_length():

    with pytest.raises(ValidationError):

        NotificationCreateRequest(
            title="A",
            message="Valid message",
            type=NotificationType.SYSTEM,
        )


# ============================================================
# SHORT MESSAGE
# ============================================================


def test_message_must_have_minimum_length():

    with pytest.raises(ValidationError):

        NotificationCreateRequest(
            title="Valid title",
            message="A",
            type=NotificationType.SYSTEM,
        )


# ============================================================
# LONG TITLE
# ============================================================


def test_title_cannot_exceed_150_characters():

    with pytest.raises(ValidationError):

        NotificationCreateRequest(
            title="A" * 151,
            message="Valid message",
            type=NotificationType.SYSTEM,
        )


# ============================================================
# LONG MESSAGE
# ============================================================


def test_message_cannot_exceed_2000_characters():

    with pytest.raises(ValidationError):

        NotificationCreateRequest(
            title="Valid title",
            message="A" * 2001,
            type=NotificationType.SYSTEM,
        )


# ============================================================
# INVALID TYPE
# ============================================================


def test_invalid_notification_type_rejected():

    with pytest.raises(ValidationError):

        NotificationCreateRequest(
            title="Test",
            message="Test message",
            type="INVALID",
        )


# ============================================================
# INVALID PRIORITY
# ============================================================


def test_invalid_notification_priority_rejected():

    with pytest.raises(ValidationError):

        NotificationCreateRequest(
            title="Test",
            message="Test message",
            type=NotificationType.SYSTEM,
            priority="INVALID",
        )


# ============================================================
# EXTRA FARMER ID REJECTED
#
# Security:
# Client must not choose farmer_id.
# ============================================================


def test_farmer_id_is_rejected():

    with pytest.raises(ValidationError):

        NotificationCreateRequest(
            title="Test",
            message="Test message",
            type=NotificationType.SYSTEM,
            farmer_id="some-id",
        )


# ============================================================
# ALL TYPES
# ============================================================


@pytest.mark.parametrize(
    "notification_type",
    [
        NotificationType.AI_ADVISOR,
        NotificationType.WEATHER,
        NotificationType.SYSTEM,
        NotificationType.GOVERNMENT,
        NotificationType.DISEASE,
    ],
)
def test_all_notification_types_are_accepted(
    notification_type,
):

    request = NotificationCreateRequest(
        title="Test",
        message="Test message",
        type=notification_type,
    )

    assert request.type == notification_type


# ============================================================
# ALL PRIORITIES
# ============================================================


@pytest.mark.parametrize(
    "priority",
    [
        NotificationPriority.HIGH,
        NotificationPriority.MEDIUM,
        NotificationPriority.LOW,
    ],
)
def test_all_priorities_are_accepted(priority):

    request = NotificationCreateRequest(
        title="Test",
        message="Test message",
        type=NotificationType.SYSTEM,
        priority=priority,
    )

    assert request.priority == priority


# ============================================================
# ENUM VALUES
# ============================================================


def test_notification_type_values():

    assert NotificationType.AI_ADVISOR.value == "AI_ADVISOR"
    assert NotificationType.WEATHER.value == "WEATHER"
    assert NotificationType.SYSTEM.value == "SYSTEM"
    assert NotificationType.GOVERNMENT.value == "GOVERNMENT"
    assert NotificationType.DISEASE.value == "DISEASE"


def test_notification_priority_values():

    assert NotificationPriority.HIGH.value == "HIGH"
    assert NotificationPriority.MEDIUM.value == "MEDIUM"
    assert NotificationPriority.LOW.value == "LOW"