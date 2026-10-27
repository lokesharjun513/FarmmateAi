from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.database.session import get_db

from app.modules.identity.models import User

from app.modules.farmer.repository import FarmerRepository

from app.modules.onboarding.schemas import OnboardingStep
from app.modules.onboarding.service import get_next_step

router = APIRouter(
    prefix="/onboarding",
    tags=["AI Onboarding"],
)


@router.get(
    "/next",
    response_model=OnboardingStep,
)
def next_step(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = FarmerRepository(db)

    farmer = repository.get_by_user_id(current_user.id)

    return get_next_step(farmer)