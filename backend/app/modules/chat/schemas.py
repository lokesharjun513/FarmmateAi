from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.chat.models import (
    AskFMRole,
    AskFMSessionStatus,
)


#
# Chat
#

class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


class ChatResponse(BaseModel):
    answer: str


#
# Session
#

class AskFMSessionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    status: AskFMSessionStatus

    started_at: datetime

    last_activity_at: datetime

    expires_at: datetime


#
# Message
#

class AskFMMessageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    role: AskFMRole

    content: str

    created_at: datetime


#
# Chat History
#

class ChatHistoryResponse(BaseModel):
    session: AskFMSessionResponse

    messages: list[AskFMMessageResponse]