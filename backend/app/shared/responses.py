# app/shared/responses.py

from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper used across FarmMate AI.
    """

    success: bool

    message: str

    data: T | None = None

    errors: list[str] = Field(
        default_factory=list,
    )