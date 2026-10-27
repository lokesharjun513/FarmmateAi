import uuid

from sqlalchemy import ForeignKey
from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.shared.mixins import TimestampMixin

from .enums import (
    WorkflowState,
    WorkflowStatus,
    WorkflowType,
)


class AIWorkflow(
    Base,
    TimestampMixin,
):
    __tablename__ = "ai_workflows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farmers.id", ondelete="CASCADE"),
        nullable=False,
    )

    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="SET NULL"),
    )

    crop_season_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crop_seasons.id", ondelete="SET NULL"),
    )

    workflow_type: Mapped[WorkflowType] = mapped_column(
        Enum(WorkflowType),
        nullable=False,
    )

    current_state: Mapped[WorkflowState] = mapped_column(
        Enum(WorkflowState),
        default=WorkflowState.IDLE,
    )

    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus),
        default=WorkflowStatus.ACTIVE,
    )

    workflow_data: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
    )

    farmer = relationship("Farmer")

    farm = relationship("Farm")

    crop_season = relationship("CropSeason")