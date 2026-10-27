from enum import Enum

from pydantic import BaseModel


class AdvicePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DailyAdvisorResponse(BaseModel):
    summary: str

    warnings: list[str]

    recommendations: list[str]

    priority: AdvicePriority