import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.shared.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.modules.farmer.models import Farmer

class DeviceToken(Base, TimestampMixin):
    __tablename__ = "device_tokens"

    __table_args__ = (
        Index("ix_device_token_fid", "fid", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farmers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    fid: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    device_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    farmer: Mapped[Farmer] = relationship(
        "Farmer",
        back_populates="device_tokens",
    )
