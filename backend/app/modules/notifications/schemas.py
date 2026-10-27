from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ============================================================
# NOTIFICATION TYPE
# ============================================================


class NotificationType(str, Enum):
    """
    Defines the source/category of a notification.
    """

    AI_ADVISOR = "AI_ADVISOR"
    WEATHER = "WEATHER"
    SYSTEM = "SYSTEM"
    GOVERNMENT = "GOVERNMENT"
    DISEASE = "DISEASE"


# ============================================================
# NOTIFICATION PRIORITY
# ============================================================


class NotificationPriority(str, Enum):
    """
    Defines the importance of a notification.
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================================
# CREATE NOTIFICATION
#
# farmer_id is intentionally NOT accepted here.
#
# The authenticated farmer is determined by the router/service.
# ============================================================


class NotificationCreateRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
    )

    # ========================================================
    # TITLE
    # ========================================================

    title: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    # ========================================================
    # MESSAGE
    # ========================================================

    message: str = Field(
        ...,
        min_length=2,
        max_length=2000,
    )

    # ========================================================
    # NOTIFICATION TYPE
    # ========================================================

    type: NotificationType

    # ========================================================
    # PRIORITY
    # ========================================================

    priority: NotificationPriority = (
        NotificationPriority.MEDIUM
    )

    # ========================================================
    # TEXT VALIDATION
    #
    # Trim leading/trailing whitespace.
    # Reject empty values.
    # Reject values shorter than the required length
    # after trimming.
    # ========================================================

    @field_validator(
        "title",
        "message",
    )
    @classmethod
    def validate_text(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Value cannot be empty."
            )

        return value


# ============================================================
# NOTIFICATION RESPONSE
# ============================================================


class NotificationResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    # ========================================================
    # IDENTITY
    # ========================================================

    id: UUID

    farmer_id: UUID

    # ========================================================
    # INFORMATION
    # ========================================================

    title: str

    message: str

    # ========================================================
    # CLASSIFICATION
    # ========================================================

    type: NotificationType

    priority: NotificationPriority

    # ========================================================
    # READ STATUS
    # ========================================================

    is_read: bool

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at: datetime

    updated_at: datetime


# ============================================================
# UNREAD COUNT RESPONSE
# ============================================================


class NotificationUnreadCountResponse(BaseModel):

    unread_count: int = Field(
        ...,
        ge=0,
    )


# ============================================================
# DEVICE TOKEN
# ============================================================


class DeviceTokenRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fid: str = Field(..., min_length=1, max_length=255)
    device_name: str | None = Field(None, max_length=100)

    @field_validator("fid")
    @classmethod
    def validate_fid(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FID cannot be empty.")
        return value
