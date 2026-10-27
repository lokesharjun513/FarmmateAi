from pydantic import BaseModel


class OnboardingStep(BaseModel):
    step: str
    title: str
    message: str
    progress: int
    completed: bool